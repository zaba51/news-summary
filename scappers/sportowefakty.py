from scappers import generic_scrapper

TITLE_CLASS = 'title'
LEAD_CLASS = 'lead'
PART_CLASS = 'contentparts'
PARAGRAPH_CLASS = 'contentpart--text'

def scrape_text_from_content(content: str):
    return generic_scrapper.scrape_text_from_content(
        content,
        title_class=TITLE_CLASS,
        lead_class=LEAD_CLASS,
        part_class=PART_CLASS,
        paragraph_class=PARAGRAPH_CLASS,
    )