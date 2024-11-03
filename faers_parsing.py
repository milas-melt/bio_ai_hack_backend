import pandas as pd
import json
from pathlib import Path
import logging
from typing import Dict, List, Any
from datetime import datetime
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FAERSToJSONConverter:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.delimiter = '$'
        
    def read_ascii_file(self, file_path: Path, columns: List[str]) -> pd.DataFrame:
        try:
            df = pd.read_csv(
                file_path,
                sep=self.delimiter,
                names=columns,
                dtype=str,
                na_values=[''],
                encoding='latin1',
                quoting=3
            )
            
            df = df.replace({r'\n': ' ', r'\r': ' '}, regex=True)
            
            df = df.replace({'': None})
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
            raise

    def process_quarter(self, quarter: str) -> Dict[str, Any]:
        """
        Process all FAERS files for a specific quarter and create structured JSON
        
        Args:
            quarter (str): Quarter identifier (e.g., '23Q1' for 2023 Q1)
            
        Returns:
            Dict: Structured JSON data
        """
        file_configs = {
            f'DEMO{quarter}.txt': {
                'name': 'demographics',
                'columns': [
                    'primaryid', 'caseid', 'caseversion', 'i_f_cod', 'event_dt',
                    'mfr_dt', 'init_fda_dt', 'fda_dt', 'rept_cod', 'auth_num',
                    'mfr_num', 'mfr_sndr', 'lit_ref', 'age', 'age_cod', 'age_grp',
                    'sex', 'e_sub', 'wt', 'wt_cod', 'rept_dt', 'to_mfr', 'occp_cod',
                    'reporter_country', 'occr_country'
                ]
            },
            f'DRUG{quarter}.txt': {
                'name': 'drugs',
                'columns': [
                    'primaryid', 'caseid', 'drug_seq', 'role_cod', 'drugname',
                    'prod_ai', 'val_vbm', 'route', 'dose_vbm', 'cum_dose_chr',
                    'cum_dose_unit', 'dechal', 'rechal', 'lot_num', 'exp_dt',
                    'nda_num', 'dose_amt', 'dose_unit', 'dose_form', 'dose_freq'
                ]
            },
            f'REAC{quarter}.txt': {
                'name': 'reactions',
                'columns': ['primaryid', 'caseid', 'pt', 'drug_rec_act']
            },
            f'OUTC{quarter}.txt': {
                'name': 'outcomes',
                'columns': ['primaryid', 'caseid', 'outc_cod']
            },
            f'RPSR{quarter}.txt': {
                'name': 'report_sources',
                'columns': ['primaryid', 'caseid', 'rpsr_cod']
            },
            f'THER{quarter}.txt': {
                'name': 'therapies',
                'columns': [
                    'primaryid', 'caseid', 'dsg_drug_seq', 'start_dt', 'end_dt',
                    'dur', 'dur_cod'
                ]
            },
            f'INDI{quarter}.txt': {
                'name': 'indications',
                'columns': ['primaryid', 'caseid', 'indi_drug_seq', 'indi_pt']
            }
        }
        
        dataframes = {}
        for filename, config in file_configs.items():
            file_path = self.data_dir / filename
            if file_path.exists():
                logger.info(f"Reading {filename}...")
                dataframes[config['name']] = self.read_ascii_file(file_path, config['columns'])
            else:
                logger.warning(f"File not found: {filename}")
                dataframes[config['name']] = pd.DataFrame(columns=config['columns'])



        
        logger.info("Processing data using DataFrame operations...")
        
        # Merge drugs with therapies and indications
        drugs_with_therapies = pd.merge(
            dataframes['drugs'],
            dataframes['therapies'],
            left_on=['primaryid', 'drug_seq'],
            right_on=['primaryid', 'dsg_drug_seq'],
            how='left'
        )

        
        drugs_complete = pd.merge(
            drugs_with_therapies,
            dataframes['indications'],
            left_on=['primaryid', 'drug_seq'],
            right_on=['primaryid', 'indi_drug_seq'],
            how='left'
        )

        # Group all related data by primaryid
        result = (
            dataframes['demographics']
            .set_index('primaryid')
            .assign(
                drugs=drugs_complete.groupby('primaryid').apply(lambda x: x.to_dict('records')),
                reactions=dataframes['reactions'].groupby('primaryid').apply(lambda x: x.to_dict('records')),
                outcomes=dataframes['outcomes'].groupby('primaryid').apply(lambda x: x.to_dict('records')),
                report_sources=dataframes['report_sources'].groupby('primaryid').apply(lambda x: x.to_dict('records'))
            )
        ).reset_index()

        logger.info("Done ouuhhooo")


        # Convert to final format
        cases = result.to_dict('records')
        
        
        final_data = {
            'metadata': {
                'quarter': quarter,
                'total_cases': len(cases),
                'export_date': datetime.now().isoformat(),
            },
            'cases': cases
        }

        return final_data

def main():
    data_dir = "ASCII" 
    quarter = "24Q3" 
    output_file = f"new_faers_{quarter}.json"
    
    try:
        converter = FAERSToJSONConverter(data_dir)
        json_data = converter.process_quarter(quarter)
        
        logger.info(f"Saving data to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully processed {json_data['metadata']['total_cases']} cases")
        
    except Exception as e:
        logger.error(f"Error processing FAERS data: {str(e)}")

if __name__ == "__main__":
    main()