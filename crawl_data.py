import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def clean_excel_text(text):
    if text is None:
        return ""

    text = str(text)
    # Xóa các ký tự điều khiển Excel không cho phép
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]","",text)

    return text.strip()

session = requests.Session()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
              "image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://bonbanh.com/",
    "Connection": "keep-alive"
}

BASE_URL = "https://bonbanh.com"

# Các cột muốn giữ
DESIRED_COLUMNS = [
    "Hãng Xe",
    "Model",
    "Giá Niêm Yết",
    "Năm sản xuất",
    "Tình trạng",
    "Số Km đã đi",
    "Xuất xứ",
    "Kiểu dáng",
    "Hộp số",
    "Động cơ",
    "Màu ngoại thất",
    "Màu nội thất",
    "Số chỗ ngồi",
    "Số cửa",
    "Dẫn động",
    "Link",
    "Mô tả"
]


def get_car_detail_data(detail_url):
    car_data = {}

    try:
        resp = session.get(detail_url,headers=HEADERS,timeout=10)

        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.content,"html.parser")

        # 1. LINK
        # =====================================================

        car_data["Link"] = detail_url

        # 2. TÊN XE + GIÁ
        # =====================================================

        title_div = soup.find("div",class_="title")

        h1_tag = (title_div.find("h1") if title_div else soup.find("h1") )

        if not h1_tag:
            return None

        full_h1_text = h1_tag.get_text(" ",strip=True)

        if "-" in full_h1_text:
            parts = full_h1_text.rsplit("-", 1)
            raw_car_name = parts[0].strip()
            raw_price = parts[1].strip()

        else:
            raw_car_name = full_h1_text
            raw_price = "Thỏa thuận"

        clean_car_name = re.sub(r"^Xe\s+","",raw_car_name,flags=re.IGNORECASE)

        ###
        words = clean_car_name.split()
        mark = words[0] if len(words) > 0 else ""
        model = words[1] if len(words) > 1 else ""
        ###

        ###
        # words = clean_car_name.split("-")
        # mark = words[0] if len(words) > 0 else ""
        # model = " ".join(words[1:]) if len(words) > 1 else ""



        car_data["Hãng Xe"] = mark
        car_data["Model"] = model
        car_data["Giá Niêm Yết"] = raw_price

        # =====================================================
        # 3. THÔNG SỐ XE
        # =====================================================

        rows = soup.find_all(
            "div",
            id="mail_parent"
        )

        for row in rows:

            label_tag = row.find("label")
            inp_tag = row.find("span",class_="inp")

            if label_tag and inp_tag:

                key = label_tag.get_text(" ",strip=True).replace(":", "").strip()

                value = inp_tag.get_text(" ",strip=True).replace("\xa0", " ")

                if key:
                    car_data[key] = value

        # 4. MÔ TẢ
        # =====================================================

        description = ""

        # Một số class có thể chứa mô tả
        description_candidates = [
            soup.find("div", class_="des_detail"),
            soup.find("div", class_="description"),
            soup.find("div", class_="des"),
            soup.find("div", id="description"),
        ]

        for candidate in description_candidates:

            if candidate:

                text = candidate.get_text("\n",strip=True)

                if len(text) > len(description):
                    description = text

        # 5. TÌM THEO TIÊU ĐỀ "MÔ TẢ"
        # =====================================================

        if not description:

            for tag in soup.find_all(["div", "section", "p", "h2", "h3"]):

                text = tag.get_text(" ",strip=True)

                if text.lower() in [
                    "mô tả",
                    "mô tả xe",
                    "thông tin mô tả"
                ]:

                    parent = tag.parent

                    if parent:
                        candidate_text = parent.get_text("\n",strip=True)

                        if len(candidate_text) > len(description):
                            description = candidate_text

        car_data["Mô tả"] = description

        return car_data

    except Exception as e:

        print(f"Lỗi cào link {detail_url}: {e}")

        return None


def crawl_bonbanh_chuanchinh(max_pages=1,output_file=None):

    all_cars = []

    # Khởi tạo session
    # =========================================================

    try:

        session.get(BASE_URL,headers=HEADERS,timeout=10)

        time.sleep(1)

    except Exception:
        pass

    # Crawl từng trang
    # =========================================================

    for page in range(1,max_pages + 1):

        url = (f"{BASE_URL}/oto/page,{page}"if page > 1 else f"{BASE_URL}/oto")

        print(f"--> [Trang {page}] "f"Đang quét danh sách bài đăng...")

        try:

            resp = session.get(url,headers=HEADERS,timeout=10)
            if resp.status_code != 200:

                print(f"HTTP {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.content,"html.parser")

            # Lấy link xe
            # =================================================

            links = []

            for a in soup.find_all("a",href=True):

                href = a["href"]

                if "/xe-" in href or "xe-" in href:

                    if href.startswith("http"):
                        full_link = href
                    else:
                        full_link = (BASE_URL + "/" + href.lstrip("/"))

                    links.append(full_link)

            # Loại trùng nhưng giữ thứ tự
            links = list(dict.fromkeys(links))

            print(f"--> Phát hiện {len(links)} xe...")

            # Crawl từng xe
            # =================================================

            for idx, car_link in enumerate(links,1):

                print(
                    f"    [{idx}/{len(links)}] "
                    f"Đang lấy: {car_link}"
                )

                car_info = get_car_detail_data(car_link)

                if car_info:
                    all_cars.append(car_info)
                time.sleep(1)

        except Exception as e:

            print(f"Lỗi trang {page}: {e}")

        time.sleep(2)

    # Xuất Excel
    # =========================================================

    if all_cars:

        df = pd.DataFrame(all_cars)

        # Chỉ giữ đúng các cột mong muốn
        existing_cols = [col for col in DESIRED_COLUMNS if col in df.columns ]

        df = df[existing_cols]

        df = df.map(lambda x: clean_excel_text(x) if isinstance(x, str) else x)

        # Ghi Excel
        with pd.ExcelWriter( output_file, engine="openpyxl") as writer:

            df.to_excel(writer,index=False,sheet_name="Danh Sách Xe")

            worksheet = writer.sheets["Danh Sách Xe"]

            # =================================================
            # Chỉnh độ rộng cột
            # =================================================

            for col in worksheet.columns:

                max_len = max(len(str(cell.value or "")) for cell in col)

                col_letter = (col[0].column_letter)

                header = (col[0].value)

                # Cột mô tả
                if header == "Mô tả":
                    width = 80

                # Cột link
                elif header == "Link":
                    width = 60

                else:
                    width = max(max_len + 3, 12)

                worksheet.column_dimensions[col_letter].width = width

        print(f"\n✅ ĐÃ XUẤT FILE EXCEL: "f"{output_file}")
        print(f"   Tổng số xe: {len(df)}")

    else:

        print("\n❌ Không lấy được dữ liệu.")

if __name__ == "__main__":

    crawl_bonbanh_chuanchinh(max_pages=1400,output_file="danh_sach_xe_bonbanh_4.xlsx")