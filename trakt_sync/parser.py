import csv
from typing import List, Generator
from .models import Movie

def parse_csv(filepath: str, file_type: str = 'watchlist') -> Generator[Movie, None, None]:
    """
    Parses a Letterboxd export CSV file and yields Movie objects.
    
    Args:
        filepath: Path to the CSV file.
        file_type: Type of export ('watchlist', 'ratings', 'watched', 'likes').
        
    Yields:
        Movie objects.
    """
    with open(filepath, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if not row.get('Name') or not row.get('Year'):
                continue
                
            title = row['Name']
            year = int(row['Year'])
            uri = row['Letterboxd URI']
            
            movie = Movie(title=title, year=year, uri=uri)
            
            if file_type == 'ratings':
                if row.get('Rating'):
                    movie.rating = float(row['Rating'])
                if row.get('Date'):
                    movie.watched_at = row['Date']
            
            if file_type == 'watched' and row.get('Date'):
                movie.watched_at = row['Date'] # Format is YYYY-MM-DD which Trakt accepts
                
            yield movie
