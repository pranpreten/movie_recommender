from pathlib import Path
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from similarity import Recommender


class App:
    def __init__(self, root):
        self.root = root
        root.title('영화 취향 검색')
        root.geometry('1050x720')
        root.minsize(850, 600)
        self.model = Recommender(Path(__file__).with_name('catalog.csv'))
        self.results = []
        self.visible = []
        self.search = tk.StringVar()
        self.genre = tk.StringVar(value='전체')
        self.status = tk.StringVar()
        header = ttk.Frame(root, padding=16)
        header.pack(fill='x')
        ttk.Label(header, text='영화 취향 검색', font=('맑은 고딕', 19, 'bold')).pack(side='left')
        ttk.Button(header, text='영화 CSV 불러오기', command=self.import_csv).pack(side='right')
        ttk.Label(root, text='좋아하는 영화를 고르거나 원하는 분위기를 입력하세요. 장르·키워드·소개글로 유사도를 계산합니다.', padding=(16, 0)).pack(anchor='w')
        form = ttk.Frame(root, padding=16)
        form.pack(fill='x')
        ttk.Entry(form, textvariable=self.search, width=45).pack(side='left', fill='x', expand=True)
        ttk.Button(form, text='내용으로 추천', command=self.query_recommend).pack(side='left', padx=8)
        self.genre_box = ttk.Combobox(form, textvariable=self.genre, state='readonly', width=12)
        self.genre_box.pack(side='left')
        self.genre_box.bind('<<ComboboxSelected>>', lambda event: self.filter_titles())
        body = ttk.Panedwindow(root, orient='horizontal')
        body.pack(fill='both', expand=True, padx=16)
        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=2)
        ttk.Label(left, text='영화 목록 · 두 번 클릭하면 추천').pack(anchor='w', pady=(0, 8))
        listing = ttk.Frame(left)
        listing.pack(fill='both', expand=True)
        self.listbox = tk.Listbox(listing, font=('맑은 고딕', 11), exportselection=False, activestyle='none')
        scroll = ttk.Scrollbar(listing, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.listbox.bind('<Double-Button-1>', lambda event: self.selected_recommend())
        ttk.Button(left, text='선택 영화로 추천', command=self.selected_recommend).pack(fill='x', pady=10)
        ttk.Label(right, text='추천 결과 · 유사도는 선호 확률이 아닙니다').pack(anchor='w', pady=(0, 8), padx=12)
        self.tree = ttk.Treeview(right, columns=('title', 'year', 'score'), show='headings', height=7)
        for column, label, width in [('title', '영화', 250), ('year', '연도', 60), ('score', '유사도', 85)]:
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor='w' if column == 'title' else 'center')
        self.tree.pack(fill='x', padx=12)
        self.tree.bind('<<TreeviewSelect>>', self.show_detail)
        self.detail = tk.Text(right, height=10, wrap='word', font=('맑은 고딕', 11), padx=12, pady=12, relief='flat', state='disabled')
        self.detail.pack(fill='both', expand=True, padx=12, pady=12)
        ttk.Button(right, text='추천 결과 CSV 저장', command=self.export).pack(anchor='e', padx=12, pady=(0, 10))
        ttk.Label(root, textvariable=self.status, padding=16).pack(fill='x')
        self.search.trace_add('write', lambda *args: self.filter_titles())
        self.refresh_catalog()
        self.listbox.selection_set(0)
        self.selected_recommend()

    def refresh_catalog(self):
        genres = sorted({genre for movie in self.model.movies for genre in movie['genres'].split('|') if genre})
        self.genre_box.configure(values=['전체'] + genres)
        self.genre.set('전체')
        self.search.set('')
        self.filter_titles()
        self.status.set(f'{len(self.model.movies)}편 로드 · 기본 CSV는 직접 작성한 소규모 예제 데이터입니다.')

    def filter_titles(self):
        query = self.search.get().strip().lower()
        genre = self.genre.get()
        self.visible = [i for i, movie in enumerate(self.model.movies) if (not query or query in movie['title'].lower()) and (genre == '전체' or genre in movie['genres'].split('|'))]
        self.listbox.delete(0, 'end')
        for index in self.visible:
            movie = self.model.movies[index]
            self.listbox.insert('end', f"{movie['title']} ({movie['year']})")

    def selected_recommend(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo('영화 선택', '목록에서 영화를 선택하세요. 원하는 내용을 입력했다면 내용으로 추천을 누르세요.')
            return
        index = self.visible[selected[0]]
        self.results = self.model.recommend(index=index, genre=self.genre.get())
        self.render(f"'{self.model.movies[index]['title']}'와 비슷한 영화")

    def query_recommend(self):
        if not self.search.get().strip():
            messagebox.showinfo('내용 입력', '예: 우주 탐사 가족, 범죄 추리 반전')
            return
        self.results = self.model.recommend(query=self.search.get(), genre=self.genre.get())
        self.render(f"검색: {self.search.get().strip()}")

    def render(self, message):
        self.tree.delete(*self.tree.get_children())
        for i, result in enumerate(self.results):
            movie = result['movie']
            self.tree.insert('', 'end', iid=str(i), values=(movie['title'], movie['year'], f"{result['score']:.3f}"))
        self.status.set(f'{message} · {len(self.results)}편')
        self.detail.configure(state='normal')
        self.detail.delete('1.0', 'end')
        self.detail.insert('end', '일치하는 결과가 없습니다. 다른 단어나 장르를 선택하세요.' if not self.results else '')
        self.detail.configure(state='disabled')
        if self.results:
            self.tree.selection_set('0')
            self.show_detail()

    def show_detail(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        result = self.results[int(selected[0])]
        movie = result['movie']
        text = f"{movie['title']} ({movie['year']})\n{movie['genres'].replace('|', ' · ')}\n\n{movie['description']}\n\n키워드: {movie['keywords']}\n\n겹치는 표현: {', '.join(result['terms'])}"
        self.detail.configure(state='normal')
        self.detail.delete('1.0', 'end')
        self.detail.insert('end', text)
        self.detail.configure(state='disabled')

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[('CSV', '*.csv')])
        if not path:
            return
        try:
            model = Recommender(path)
        except (OSError, ValueError, csv.Error) as exc:
            messagebox.showerror('불러오기 실패', str(exc))
            return
        self.model = model
        self.results = []
        self.render('새 데이터')
        self.refresh_catalog()

    def export(self):
        if not self.results:
            messagebox.showinfo('저장', '추천 결과를 먼저 만들어 주세요.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', initialfile='recommendations.csv', filetypes=[('CSV', '*.csv')])
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['title', 'year', 'genres', 'similarity', 'description'])
                for row in self.results:
                    movie = row['movie']
                    values = [movie['title'], movie['year'], movie['genres'], f"{row['score']:.6f}", movie['description']]
                    writer.writerow(["'"+value if value.startswith(('=', '+', '-', '@')) else value for value in values])
            self.status.set(f'저장 완료 · {Path(path).name}')
        except OSError as exc:
            messagebox.showerror('저장 실패', str(exc))


if __name__ == '__main__':
    root = tk.Tk()
    ttk.Style().configure('.', font=('맑은 고딕', 10))
    App(root)
    root.mainloop()
