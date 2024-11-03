import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import pandas as pd
from Bio import Entrez
from Bio import Medline
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
import json
import time


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pubmed_rag.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PatientData:
    age: int
    gender: str
    weight: float
    existing_conditions: List[str]
    medications: List[str]

class ProgressTracker:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProgressTracker, cls).__new__(cls)
            cls._instance._progress = 0
            cls._instance._status = "Starting analysis..."
            cls._instance._details = ""
            cls._instance._is_complete = False
        return cls._instance
    
    def update(self, progress: int, status: str, details: str = ""):
        self._progress = progress
        self._status = status
        self._details = details
    
    def reset(self):
        self._progress = 0
        self._is_complete = False
        self._status = "Starting analysis..."
        
    def complete(self):
        self._is_complete = True
        self._progress = 100
        
    @property
    def current_state(self):
        return {
            "progress": self._progress,
            "status": self._status,
            "details": self._details,
            "isComplete": self._is_complete
        }



class PubMedRAGPipeline:
    def __init__(self, tracker):
        """
        Initialize the RAG pipeline.
        
        Args:
            openai_api_key: Your OpenAI API key
            email: Email for PubMed API (required by their terms of service)
        """
        api_key = "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"

        self.openai_client = openai.OpenAI(api_key=api_key)
        Entrez.email = 'lol@gamil.com'
        logger.info("Initialized PubMedRAGPipeline")
        self.cache_file = Path("embedding_cache.json")
        self.progress_tracker = tracker

        # Initialize embedding cache
        self.embedding_cache = self._load_cache()
        
    def _load_cache(self) -> Dict[str, List[float]]:
        """Load embedding cache from local file."""
        if self.cache_file.exists():
            logger.info("Loading embedding cache from file")
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Failed to load cache file, starting with empty cache")
                return {}
        return {}
    
    def _save_cache(self):
        """Save embedding cache to local file."""
        logger.info("Saving embedding cache to file")
        with open(self.cache_file, 'w') as f:
            json.dump(self.embedding_cache, f)

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI's API with retry logic."""
        if text in self.embedding_cache:
            logger.debug("Using cached embedding")
            return self.embedding_cache[text]
            
        logger.debug("Generating new embedding")
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        embedding = response.data[0].embedding
        self.embedding_cache[text] = embedding
        self._save_cache()  # Save cache after adding new embedding
        return embedding

    def search_pubmed(self, drug_name: str, max_results: int = 50) -> List[Dict]:
        """
        Search PubMed for clinical trials related to the drug.
        """
        logger.info(f"Searching PubMed for {drug_name}")
        # Search for clinical trials
        search_term = f"{drug_name}"
        handle = Entrez.esearch(db="pubmed", term=search_term, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()

        # Fetch details for each paper
        id_list = record["IdList"]
        logger.info(f"Found {len(id_list)} PubMed articles")
        handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
        records = list(Medline.parse(handle))
        handle.close()

        return records

    def process_pubmed_record(self, record: Dict) -> str:
        """
        Process a PubMed record into a structured format for embedding.
        """
        logger.debug(f"Processing PubMed record {record.get('PMID', 'unknown')}")
        title = record.get('TI', '')
        abstract = record.get('AB', '')
        chemicals = record.get('RN', '')
        mesh_terms = record.get('MH', [])
        
        structured_text = f"""
        Title: {title}
        Abstract: {abstract}
        Chemicals: {chemicals}
        MeSH Terms: {', '.join(mesh_terms) if isinstance(mesh_terms, list) else mesh_terms}
        """
        return structured_text

    def create_knowledge_base(self, drug_name: str) -> List[Dict[str, Any]]:
        """
        Create a knowledge base for a specific drug from PubMed data.
        """
        logger.info(f"Creating knowledge base for {drug_name}")
        records = self.search_pubmed(drug_name)
        knowledge_base = []
        
        for i, record in enumerate(records):
            logger.debug(f"Processing record {i+1}/{len(records)}")
            processed_text = self.process_pubmed_record(record)
            embedding = self.get_embedding(processed_text)
            
            knowledge_base.append({
                'text': processed_text,
                'embedding': embedding,
                'metadata': {
                    'pmid': record.get('PMID', ''),
                    'year': record.get('DP', ''),
                    'journal': record.get('TA', '')
                }
            })
        
        logger.info(f"Created knowledge base with {len(knowledge_base)} entries")
        return knowledge_base

    def get_relevant_contexts(
        self, 
        query: str, 
        knowledge_base: List[Dict[str, Any]], 
        n_results: int = 3
    ) -> List[str]:
        """
        Retrieve the most relevant contexts for a query using embedding similarity.
        """
        logger.info(f"Finding relevant contexts for query: {query[:50]}...")
        query_embedding = self.get_embedding(query)
        
        # Calculate similarities
        similarities = []
        for item in knowledge_base:
            similarity = cosine_similarity(
                [query_embedding], 
                [item['embedding']]
            )[0][0]
            similarities.append(similarity)
        
        # Get top results
        top_indices = np.argsort(similarities)[-n_results:][::-1]
        logger.info(f"Found {n_results} relevant contexts")
        return [knowledge_base[i]['text'] for i in top_indices]

    def generate_medical_insights(
        self, 
        patient_data: PatientData,
        drug_name: str,
        fda_data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Async version of generate_medical_insights with progress tracking
        """
        logger.info(f"Generating medical insights for {drug_name}")
        self.progress_tracker.update(15, "Creating medical knowledge base")
        time.sleep(2) 
        
        # Create knowledge base for a drug
        knowledge_base = self.create_knowledge_base(drug_name)
        
        # Create context about the patient
        patient_context = f"""
        Patient Information:
        - Age: {patient_data.age}
        - Gender: {patient_data.gender}
        - Weight: {patient_data.weight}kg
        - Existing Conditions: {', '.join(patient_data.existing_conditions)}
        - Current Medications: {', '.join(patient_data.medications)}
        """
        # Get relevant FDA adverse events
        self.progress_tracker.update(40, "Building similarity graph", "Filtering for cases similar to you")
        time.sleep(2) 
        similar_cases = self._filter_similar_cases(fda_data, patient_data)
        fda_summary = self._summarize_fda_data(patient_data, drug_name, similar_cases)
       

        # Calculate age group
        months = patient_data.age * 12
        AGE_GROUPS = {
            range(0, 1): "Neonate",
            range(1, 24): "Infant",
            range(24, 144): "Child",
            range(144, 216): "Adolescent",
            range(216, 780): "Adult",
            range(780, 1500): "Elderly"
        }
        age_grp = next((group for age_range, group in AGE_GROUPS.items() 
                       if months in age_range), "Adult")

        # Generate PubMed queries
        # Create focused sub-queries for different clinical aspects
        queries = [
            # Core safety and efficacy
            f"{drug_name} clinical trial safety efficacy {patient_data.age}",
            
            # Dosing and administration
            f"{drug_name} dosage administration {patient_data.weight} KG {age_grp}",
            
            # Specific comorbidity interactions
            *[f"{drug_name} {condition} interaction management" 
              for condition in patient_data.existing_conditions],
            
            # Drug interactions
            *[f"{drug_name} {med} drug interaction" 
              for med in patient_data.medications],
            
            # Special populations
            f"{drug_name} {patient_data.gender.lower()} specific considerations {age_grp}",
            
            # Monitoring and adverse effects
            f"{drug_name} monitoring requirements adverse effects {' '.join(patient_data.existing_conditions)}",
            
            # Long-term outcomes
            f"{drug_name} long term safety outcomes {age_grp}",
            
            # Quality of life impacts
            f"{drug_name} quality of life patient outcomes adherence",
            
            # Contraindications and warnings
            f"{drug_name} contraindications warnings precautions {' '.join(patient_data.existing_conditions)}",
            
            # Pharmacokinetics for patient profile
            f"{drug_name} pharmacokinetics absorption metabolism {patient_data.weight} KG {age_grp}"
        ]
        
        # Process PubMed queries with progress updates
        all_relevant_contexts = []
        total_queries = len(queries)

        self.progress_tracker.update(60, "Querying knowledge base", "Retrieving and analysing clincial trials")
        time.sleep(2) 
        
        all_relevant_contexts = []
        for query in queries:
            contexts = self.get_relevant_contexts(query, knowledge_base, n_results=2)
            all_relevant_contexts.extend(contexts)
            
        # Remove duplicates while preserving order
        relevant_studies = list(dict.fromkeys(all_relevant_contexts))
        relevant_studies = self.get_relevant_contexts(query, knowledge_base)    
        
        # Combine contexts and generate insights
        self.progress_tracker.update(80, "Summarising findings and computing statistics")
        time.sleep(2) 
        full_context = f"""
        {patient_context}
        
        Relevant Clinical Trial Information:
        {' '.join(relevant_studies)}
        """
        
        # Generate insights using GPT-4
        self.progress_tracker.update(90, "Summarising findings and computing statistics")
        time.sleep(2) 
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """..."""},
                {"role": "user", "content": full_context}
            ],
            temperature=0.2
        )
        
        # Prepare final output
        self.progress_tracker.update(95, "Preparing final report")
        time.sleep(2)
        output = {
            "insights": response.choices[0].message.content,
            "summary": fda_summary,
            "sources": {
                "pubmed_papers": [kb["metadata"] for kb in knowledge_base],
                "fda_cases": len(similar_cases)
            }
        }
        
        self.progress_tracker.complete()
        logger.info("Successfully generated medical insights")


        # output_filename = f"medical_insights_{drug_name.replace(' ', '_')}_{patient_data.age}_{patient_data.gender}.json"
        # with open(output_filename, 'w', encoding='utf-8') as f:
        #     json.dump(output, f, indent=4, ensure_ascii=False)
        return output




    def _filter_similar_cases(self, fda_data: List[Dict], patient_data: PatientData) -> List[Dict]:
        """
        Filter FDA cases based on patient similarity using multiple characteristics.
        Returns cases sorted by similarity score (highest first).
        """
        logger.info("Filtering similar FDA cases")

        def calculate_age_similarity(case_age):
            """Calculate similarity score for age using a gaussian function"""
            if case_age is None:
                return 0  # Default score for missing data
            age_diff = abs(case_age - patient_data.age)
            return np.exp(-(age_diff ** 2) / (2 * 10 ** 2))  # sigma=10 years
        
        def calculate_weight_similarity(case_weight):
            """Calculate similarity score for weight using a gaussian function"""
            if case_weight is None:
                return 0  # Default score for missing data
            weight_diff = abs(case_weight - patient_data.weight)
            return np.exp(-(weight_diff ** 2) / (2 * 15 ** 2))  # sigma=15 kg
        
        def calculate_gender_similarity(case_gender):
            """Calculate binary similarity score for gender"""
            if case_gender is None:
                return 0 # Default score for missing data
            try:
                return 1.0 if case_gender.lower() == patient_data.gender.lower() else 0.0
            except (AttributeError, TypeError):
                return 0 
        
        def calculate_list_similarity(case_list, patient_list):
            """Calculate Jaccard similarity between two lists"""
            if not case_list:
                return 0.5  # Default score for missing data
            
            case_set = set(x.lower() for x in case_list)
            patient_set = set(x.lower() for x in patient_list)
            
            if not patient_set or not case_set:
                return 0.5
                
            intersection = len(patient_set.intersection(case_set))
            union = len(patient_set.union(case_set))
            return intersection / union if union > 0 else 0.0

        # Calculate similarity scores for each case
        similar_cases = []
        for case in fda_data:
            similarity_score = (
                calculate_age_similarity(float(case['demographic_info'].get('age'))) +
                calculate_gender_similarity(case['demographic_info'].get('sex')) +
                calculate_weight_similarity(float(case['demographic_info'].get('wt'))) +
                calculate_list_similarity([dr['drugname'] for dr in case['drugs']], patient_data.medications)
            )
            case['similarity_score'] = similarity_score
            similar_cases.append(case)

        # Sort by similarity score and filter cases with score above threshold
        threshold = 0.3  # Adjust this threshold as needed
        filtered_cases = [
            case for case in similar_cases 
            if case['similarity_score'] >= threshold
        ]
        filtered_cases.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        logger.info(f"Found {len(filtered_cases)} similar cases above threshold {threshold}")
        
        return filtered_cases[:5]  # Return top 100 most similar cases
    
    def _format_cases_for_llm(self, patient_data, target, cases: List[Dict]) -> str:
        """Format FDA cases into a structured string for LLM processing."""
        formatted_cases = []

        out_map = {
        'DE': 'Death',
        'LT': 'Life-Threatening',
        'HO': 'Hospitalization - Initial or Prolonged',
        'DS': 'Disability',
        'CA': 'Congenital Anomaly',
        'RI': 'Required Intervention to Prevent Permanent Impairment/Damage',
        'OT': 'Other Serious (Important Medical Event)'
        }

        role_map = {
        'PS': 'Primary Suspect',
        'SS': 'Secondary Suspect',
        'I': 'Interacting',
        }
        
        
        for i, case in enumerate(cases, 1):
            drug_map = {}
            for drug in case['drugs']: 
                name = drug['drugname'].lower()
                role = drug['role_cod']

                if patient_data.medications == []:
                    if name == target and role=='PS':
                        drug_map[name] = role_map[role]
                else:
                    if name in patient_data.medications or name == target:
                        if role in ['PS', 'SS', 'I']:
                            drug_map[name] = role_map[role]
            
            outcomes = case['outcomes']
            if outcomes != []:
                outcomes = [out_map[outcome['outc_cod']] for outcome in outcomes]

            reactions = [reaction['pt'] for reaction in case['reactions']]
            case_dict = {
                'drug_role': drug_map,
                'reactions': reactions,
                'outcomes': outcomes
            }
            formatted_cases.append(json.dumps(case_dict))


        return "\n\n".join(formatted_cases)

    def _summarize_fda_data(self, patient, drug, cases: pd.DataFrame) -> str:
        """Summarize relevant FDA adverse event data."""
        logger.info("Summarizing FDA data")

        formatted_cases = self._format_cases_for_llm(patient, drug, cases)

        patient_context = f"""
        Patient Information:
        - Age: {patient.age}
        - Gender: {patient.gender}
        - Weight: {patient.weight}kg
        - Existing Conditions: {', '.join(patient.existing_conditions)}
        - Current Medications: {', '.join(patient.medications)}
        """

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""
                You are a medical research assistant. You need to provide a clear and concise summary of the risk profile for the following patient.
                {patient_context} \n
                 
                 You will be provided with a list of the closest cases as reported in the FDA Adverse Event database that are similar to that of the patient. That similarity has been computed based on the age, weight, sex and medications currently being taken. 
                 Your job is to build a summary of the adverse effect risk profile for the patient by specifying which reactions are most common and by what drugs or combination of drugs are they caused (depending on the provided drug roles) based on the medications the patient is currently taking (if any). You should also report the possible outcomes if available. 
                 The goal of this is to provide the patient with a risk assessment if they want to start taking {drug}. 

                 Important to note that if the drug_role dictionary is empty, it means that none of the drugs taht the patient is currently taking nor the one he wants to start taking are directly related to the reactions for the given case. So use carefully the drug roles to interepret the likelihood of the specific patient getting these reactions. 
                 Please create a concise summary that is easily understandable for the patient, that clearly states that we are using cases that are very similar to their demographic and taking into account their current medications. Make the summary concise and into a nice paragraph without listing everythig out. 
                """},
                {"role": "user", "content": formatted_cases}
            ],
            temperature=0.2
        )
        summary = response.choices[0].message.content
        return summary