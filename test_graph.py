from graph import graph

if __name__ == "__main__":

    while True:

        query = input("\nAsk (type 'exit' to quit): ")

        if query.lower() == "exit":
            break

        result = graph.invoke({
            "query": query
        })

        print("\n" + "=" * 60)

        print(result["final_answer"])