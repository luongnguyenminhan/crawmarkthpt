import argparse
import pandas as pd
from bs4 import BeautifulSoup
import requests
import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_soup(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup

def get_diemthi(id):
    url = f'https://diemthi.vnexpress.net/index/detail/sbd/{id}/year/2024'
    soup = get_soup(url)
    students_dict = {'id': id}
    try:
        table = soup.find('table', class_='e-table')
        rows = table.find_all('tr')
        students_dict = {'id': id}
        for row in rows[1:-1]:
            cells = row.find_all('td')
            subject = cells[0].text
            students_dict[subject] = cells[1].text.strip()

        # Check if students_dict has Lịch sử, Địa lý, GDCD:
        if 'Lịch sử' not in students_dict:
            students_dict['Lịch sử'] = None
            students_dict['Địa lý'] = None
            students_dict['Giáo dục công dân'] = None
        else:
            students_dict['Vật lý'] = None
            students_dict['Hóa học'] = None
            students_dict['Sinh học'] = None

        # Sort dict by order: Toán, Ngữ văn, Ngoại ngữ, Vật lý, Hóa học, Sinh học, Lịch sử, Địa lý, Giáo dục công dân
        students_dict = dict(sorted(students_dict.items(), key=lambda item: ['id', 'Toán', 'Ngữ văn', 'Ngoại ngữ', 'Vật lý', 'Hóa học', 'Sinh học', 'Lịch sử', 'Địa lý', 'Giáo dục công dân'].index(item[0])))
        return students_dict
    except Exception as e:
        print(f'Error for ID {id}: {e}')
        return None

def get_diemthi_list(ids):
    students = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_id = {executor.submit(get_diemthi, id): id for id in ids}
        for future in tqdm.tqdm(as_completed(future_to_id), total=len(ids)):
            id = future_to_id[future]
            try:
                student = future.result()
                if student:
                    students.append(student)
            except Exception as e:
                print(f'Error processing ID {id}: {e}')
    return students

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch exam scores based on ID range')
    parser.add_argument('--start', type=int, required=True, help='Start of the ID range')
    parser.add_argument('--end', type=int, required=True, help='End of the ID range')
    parser.add_argument('--threads', type=int, default=10, help='Number of threads to use')

    args = parser.parse_args()
    ids = range(args.start, args.end + 1)
    
    students = get_diemthi_list(ids)
    df = pd.DataFrame(students)
    df.to_csv('diemthi.csv', index=False)
