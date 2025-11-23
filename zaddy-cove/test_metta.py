from hyperon import MeTTa

def main():
    # Initialize MeTTa
    metta = MeTTa()

    # Store a fact
    metta.run('!(add-atom &self (reply-to hello Hello_from_MeTTa))')

    # Check if the fact is stored
    print("Facts in &self:")
    print(metta.run('!(get-atoms &self)'))

    # Query for the fact
    print("
Direct query:")
    query_result = metta.run('!(match &self (reply-to hello ?y) ?y)')
    print(query_result)

if __name__ == "__main__":
    main()