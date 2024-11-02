from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
import pymysql.cursors
import llm
import faers_select

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


@app.route("/dashboard", methods=["GET"])
def get_dashboard():
    age: str = request.args.get("age")
    sex: str = request.args.get("sex")
    weight: str = request.args.get("weight")
    ethnicity: str = request.args.get("ethnicity")

    age_related_cases = faers_select.select_on_age(*faers_select.select_age_bucket(int(age)))
    sex_related_cases = faers_select.select_on_sex(sex)
    weight_related_cases = faers_select.select_on_weight(*faers_select.select_weight_bucket(float(weight)))

    testimony = llm.summarise_testimonials(llm.DUMMY_TESTIMONIALS)
    return jsonify(
        {
            "patient_info": {
                "age": age,
                "weight": weight,
                "sex": sex,
                "ethnicity": ethnicity,
            },
            "probabilities": {
                "most_common": {
                    "age": {
                        "vomiting": len(age_related_cases),
                        "heart_attack": len(age_related_cases),
                    },
                    "sex": {
                        "vomiting": len(sex_related_cases),
                        "heart_attack": len(sex_related_cases),
                    },
                    "weight": {
                        "vomiting": len(weight_related_cases),
                        "heart_attack": len(weight_related_cases),
                    },
                }
            },
            "testimony": testimony,
            "actionable_insights": ["a", "b", "c"],
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
