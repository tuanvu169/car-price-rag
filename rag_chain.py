from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from config import GOOGLE_API_KEY, LLM_MODEL_NAME, TOP_K


def build_rag_chain(vectorstore):
    if not GOOGLE_API_KEY:
        raise ValueError("Chưa có GOOGLE_API_KEY trong file .env")

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )

    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        max_retries=3,
    )

    prompt = ChatPromptTemplate.from_template(
        """
Bạn là chuyên gia định giá ô tô tại Việt Nam.

Dữ liệu xe tham chiếu:
{context}

Câu hỏi:
{question}

Hãy định giá chỉ dựa trên dữ liệu trong Context.
- Ưu tiên xe cùng hãng, cùng model và năm sản xuất gần nhau.
- So sánh số km, động cơ, hộp số và tình trạng xe.
- Liệt kê xe tham chiếu phù hợp và giá tương ứng.
- Đưa ra khoảng giá tham khảo và giải thích cách ước lượng.
- Không tự bịa dữ liệu hoặc giá xe.
- Nếu dữ liệu không đủ, hãy nói rõ.
- Phân biệt giá niêm yết với giá bán thực tế nếu có thể.
- Trả lời bằng tiếng Việt.
- Kết luận bằng một mức giá. (chỉ ghi bằng số không có chữ)
"""
    )

    def format_docs(docs):
        if not docs:
            return "Không tìm thấy dữ liệu phù hợp."

        return "\n\n---\n\n".join(
            doc.page_content for doc in docs
        )

    return (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
