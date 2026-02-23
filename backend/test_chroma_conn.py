import sys
import os

# Add the current directory to sys.path to allow importing from the 'app' package
sys.path.append(os.getcwd())

from app.services.vector_service import vector_service

def test_chroma():
    try:
        print("🧪 Testing ChromaDB Connection...")
        
        # Test adding a medical case
        case_id = "test_case_1"
        symptoms = ["headache", "fever", "cough"]
        diagnosis = "Common Cold"
        treatment = "Rest and fluids"
        
        print(f"Adding test case: {case_id}...")
        add_result = vector_service.add_medical_case(
            case_id=case_id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            treatment=treatment
        )
        
        if add_result.get("success"):
            print("✅ Successfully added medical case to ChromaDB")
        else:
            print(f"❌ Failed to add medical case: {add_result.get('error')}")
            return

        # Test searching for similar cases
        print("Searching for similar cases...")
        search_results = vector_service.search_similar_cases(symptoms=["fever", "cough"])
        
        if search_results:
            print(f"✅ Found {len(search_results)} similar cases!")
            for i, result in enumerate(search_results):
                print(f"  Result {i+1}: {result['diagnosis']} (Score: {result['similarity_score']:.4f})")
        else:
            print("❌ No similar cases found.")

        # Cleanup test data
        print(f"Cleaning up test case {case_id}...")
        vector_service.delete_case(case_id)
        print("✅ Cleanup complete.")
        
    except Exception as e:
        print(f"❌ ChromaDB Test Failed.")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chroma()
