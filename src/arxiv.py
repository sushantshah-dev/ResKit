import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from typing import List, Dict, Any


def search_arxiv(query: str, category: str) -> List[Dict[str, Any]]:
    url = f'https://export.arxiv.org/api/query?search_query={category}:{quote(query)}'
    response = requests.get(url)
    root = ET.fromstring(response.content)
    results = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title')
        title = title.text.strip() if title is not None else ''
        authors = [author.find('{http://www.w3.org/2005/Atom}name').text.strip() for author in entry.findall('{http://www.w3.org/2005/Atom}author') if author.find('{http://www.w3.org/2005/Atom}name') is not None]
        summary = entry.find('{http://www.w3.org/2005/Atom}summary')
        summary = summary.text.strip() if summary is not None else ''
        pdf_link = ''
        for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
            if link.attrib.get('title') == 'pdf':
                pdf_link = link.attrib.get('href', '')
                break
        published = entry.find('{http://www.w3.org/2005/Atom}published')
        published = published.text if published is not None else ''
        arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id')
        arxiv_id = arxiv_id.text if arxiv_id is not None else ''
        results.append({
            'title': title,
            'authors': authors,
            'summary': summary,
            'pdf_link': pdf_link,
            'published': published,
            'arxiv_id': arxiv_id
        })
        
    return results

def get_arxiv_by_ids(arxiv_ids: List[str]) -> List[Dict[str, Any]]:
    id_list = ','.join(arxiv_ids)
    url = f'http://export.arxiv.org/api/query?id_list={quote(id_list)}'
    response = requests.get(url)
    root = ET.fromstring(response.content)
    results = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title')
        title = title.text.strip() if title is not None else ''
        authors = [author.find('{http://www.w3.org/2005/Atom}name').text.strip() for author in entry.findall('{http://www.w3.org/2005/Atom}author') if author.find('{http://www.w3.org/2005/Atom}name') is not None]
        summary = entry.find('{http://www.w3.org/2005/Atom}summary')
        summary = summary.text.strip() if summary is not None else ''
        pdf_link = ''
        for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
            if link.attrib.get('title') == 'pdf':
                pdf_link = link.attrib.get('href', '')
                break
        published = entry.find('{http://www.w3.org/2005/Atom}published')
        published = published.text if published is not None else ''
        arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id')
        arxiv_id = arxiv_id.text if arxiv_id is not None else ''
        results.append({
            'title': title,
            'authors': authors,
            'summary': summary,
            'pdf_link': pdf_link,
            'published': published,
            'arxiv_id': arxiv_id
        })
    return results