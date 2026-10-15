from embedding_data import get_vectorstore
from rag_chain import build_rag_chain


def main():
    vectorstore = get_vectorstore()
    rag_chain = build_rag_chain(vectorstore)

    query = "Định giá giúp tôi xe Audi Q5 sản xuất năm 2022, xe đã qua sử dụng."

    print(f"\nCâu hỏi: {query}")

    response = rag_chain.invoke(query)

    print("\nKết quả định giá:")
    print(response)


if __name__ == "__main__":
    main()
