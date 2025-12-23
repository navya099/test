class IndexLibrary:
    def __init__(self, df):
        self.df = df

    def get_index(self, filename):
        row = self.df[self.df["파일명"] == filename]
        if row.empty:
            return None
        return int(row.iloc[0]["인덱스"])

    def get_path(self, filename):
        row = self.df[self.df["파일명"] == filename]
        if row.empty:
            return None
        return row.iloc[0]["경로"]

    def search(self, keyword):
        return self.df[self.df["파일명"].str.contains(keyword, na=False)]