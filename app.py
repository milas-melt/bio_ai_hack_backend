from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
import pymysql.cursors
import pubmed_rag as pubmed_rag
import faers_select
import json
from flask import Response, stream_with_context
import time

app = Flask(__name__)
CORS(app)

# Load configurations
app.config.from_pyfile("config.py")


# Database connection function
def get_db_connection():
    try:
        conn = pymysql.connect(
            host=app.config["MYSQL_HOST"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            database=app.config["MYSQL_DB"],
        )
        return conn
    except pymysql.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


@app.route("/api/test", methods=["GET"])
def test_endpoint():
    return jsonify({"message": "Hello from Flask!"})


# ============== Main Endpoints ============

@app.route("/dashboard/progress")
def get_progress():
    def generate():
        tracker = pubmed_rag.ProgressTracker()
        tracker.reset()  # Reset at the start of progress tracking
        
        while not tracker._is_complete:
            data = tracker.current_state
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(0.5)  # Poll every 500ms
        # Send final update
        yield f"data: {json.dumps(tracker.current_state)}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )

@app.route("/dashboard", methods=["POST"])
def get_dashboard():
    data = request.get_json()
    age = data.get("age")
    sex = data.get("sex")
    weight = data.get("weight")
    conditions = data.get("conditions")
    medications = data.get('medications')
    drug_name = "ozempic"

    # Reset progress tracker for new request
    tracker = pubmed_rag.ProgressTracker()
    tracker.reset() 


    # Example patient data
    patient = pubmed_rag.PatientData(
        age=float(age),
        gender=sex,
        weight=float(weight),
        existing_conditions=conditions,
        medications=medications
    )

    tracker.update(10, "Loading and parsing FDA data")
    time.sleep(2)

    with open('./bio_ai_hack_backend/faers_ozempic_24Q3.json', 'r') as f:
            fda_data = json.load(f)['cases']
    

    pipeline = pubmed_rag.PubMedRAGPipeline(tracker)
    
    insights = pipeline.generate_medical_insights(
        patient_data=patient,
        drug_name=drug_name,
        fda_data=fda_data,
    )


    age_related_cases = faers_select.select_on_age(
        *faers_select.select_age_bucket(int(age))
    )
    sex_related_cases = faers_select.select_on_sex(sex)
    weight_related_cases = faers_select.select_on_weight(
        *faers_select.select_weight_bucket(float(weight))
    )
    medication_related_cases = faers_select.select_on_medications(patient.medications, drug_name)
    joint_related_cases = faers_select.intersection(
        age_related_cases, sex_related_cases, weight_related_cases
    )

    age_related_reactions = faers_select.top_k(
        faers_select.proportionalize(faers_select.extract_primary_key_reactions(age_related_cases))
    )
    sex_related_reactions = faers_select.top_k(
        faers_select.proportionalize(faers_select.extract_primary_key_reactions(sex_related_cases))
    )
    weight_related_reactions = faers_select.top_k(
        faers_select.proportionalize(
            faers_select.extract_primary_key_reactions(weight_related_cases)
        )
    )
    medication_related_reactions =  faers_select.top_k(
        faers_select.proportionalize(
            faers_select.extract_primary_key_reactions(medication_related_cases)
        )
    )
    joint_related_reactions = faers_select.top_k(
        faers_select.proportionalize(
            faers_select.extract_primary_key_reactions(joint_related_cases)
        )
    )
    # testimony = llm.summarise_testimonials(llm.DUMMY_TESTIMONIALS)
    return jsonify(
        {
            "patient_info": {
                "age": age,
                "weight": weight,
                "sex": sex,
                "conditions": conditions,
                "medications": medications,
            },
            "probabilities": {
                "most_common": [
                    ("age weight sex", joint_related_reactions),
                    ("age", age_related_reactions),
                    ("sex", sex_related_reactions),
                    ("weight", weight_related_reactions),
                    ("medications", medication_related_reactions),
                ]
            },
            "summary": insights['summary'],
            "actionable_insights": insights['insights'],
        }
    )


# =============== CRUD ITEMS ===============
@app.route("/api/items", methods=["GET"])
def get_items():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(items)


@app.route("/api/items", methods=["POST"])
def add_item():
    new_item_name = request.json["name"]
    try:
        conn = get_db_connection()
        if conn is None:
            raise Exception("Database connection failed")
        cursor = conn.cursor()
        # Insert the new item into the database
        cursor.execute("INSERT INTO items (name) VALUES (%s)", (new_item_name,))
        conn.commit()
        # Get the ID of the newly inserted item
        new_item_id = cursor.lastrowid
        cursor.close()
        conn.close()
        # Return the new item's ID and name
        return jsonify({"id": new_item_id, "name": new_item_name}), 201
    except Exception as e:
        app.logger.error(f"Error adding item: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    updated_name = request.json.get("name")
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    # Check if item exists
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    item = cursor.fetchone()

    if not item:
        cursor.close()
        conn.close()
        return jsonify({"error": "Item not found"}), 404

    cursor.execute("UPDATE items SET name = %s WHERE id = %s", (updated_name, item_id))
    conn.commit()

    # Return the updated item
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    updated_item = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(updated_item)


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Item deleted successfully"})


# ============================================

if __name__ == "__main__":
    app.run(debug=True, port=5050)
