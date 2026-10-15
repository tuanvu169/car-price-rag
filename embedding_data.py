import shutil
import pandas as pd

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from config import (
    EXCEL_FILE,
    CHROMA_DB_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_DEVICE,
    REBUILD_VECTOR_DB,
)


def convert_data_to_documents(file_path):
    df = pd.read_excel(file_path)
    print(f"Tổng số xe: {len(df)}")

    documents = []

    for idx, row in df.iterrows():

        def val(name):
            value = row.get(name, "")
            return "" if pd.isna(value) else str(value).strip()

        brand = val("Hãng Xe")
        model = val("Model")
        price = val("Giá Niêm Yết")
        year = val("Năm sản xuất")
        condition = val("Tình trạng")
        km = val("Số Km đã đi")
        origin = val("Xuất xứ")
        body = val("Kiểu dáng")
        gearbox = val("Hộp số")
        engine = val("Động cơ")
        exterior = val("Màu ngoại thất")
        interior = val("Màu nội thất")
        seats = val("Số chỗ ngồi")
        drive = val("Dẫn động")

        text = (
            f"Thông tin xe {brand} {model}:\n"
            f"- Hãng sản xuất: {brand}\n"
            f"- Dòng xe: {model}\n"
            f"- Giá niêm yết / giá bán: {price}\n"
            f"- Năm sản xuất: {year}\n"
            f"- Tình trạng: {condition}\n"
            f"- Số Km đã đi: {km}\n"
            f"- Xuất xứ: {origin}\n"
            f"- Kiểu dáng: {body}\n"
            f"- Hộp số: {gearbox}\n"
            f"- Động cơ: {engine}\n"
            f"- Màu ngoại thất: {exterior}\n"
            f"- Màu nội thất: {interior}\n"
            f"- Số chỗ ngồi: {seats}\n"
            f"- Dẫn động: {drive}"
        )

        metadata = {
            "row_id": int(idx),
            "brand": brand,
            "model": model,
            "price": price,
            "year": year,
            "km": km,
            "engine": engine,
            "color": exterior,
            "condition": condition,
            "gearbox": gearbox,
        }

        documents.append(
            Document(page_content=text, metadata=metadata)
        )

    return documents


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": EMBEDDING_DEVICE},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_vectorstore():
    embeddings = get_embeddings()

    # Nếu ChromaDB đã tồn tại, nạp lại database
    if CHROMA_DB_DIR.exists() and not REBUILD_VECTOR_DB:
        vectorstore = Chroma(
            persist_directory=str(CHROMA_DB_DIR),
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )

        if vectorstore._collection.count() > 0:
            print("Đã nạp ChromaDB có sẵn.")
            print(f"Số vector: {vectorstore._collection.count()}")
            return vectorstore

    # Chỉ tạo mới khi chưa có database hoặc yêu cầu rebuild
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {EXCEL_FILE}")

    documents = convert_data_to_documents(EXCEL_FILE)

    if not documents:
        raise ValueError("File Excel không có dữ liệu.")

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(CHROMA_DB_DIR),
        collection_name=COLLECTION_NAME,
    )

    print("Đã tạo ChromaDB mới.")
    print(f"Số vector: {vectorstore._collection.count()}")

    return vectorstore
