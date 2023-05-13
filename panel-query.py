import panel as pn
from langchain.vectorstores.faiss import FAISS
from pathlib import Path
from pickle import load

def load_vectorstore():
    vectorstore_path = Path('vectorstore.pypickle')
    with vectorstore_path.open('rb') as file:
        vectorstore = load(file)
    return vectorstore

def run_query(event, text_input_query, rows_results, vectorstore):
    query = text_input_query.value
    docs = vectorstore.similarity_search(query)
    for i, doc in enumerate(docs[:len(rows_results)]):
        rows_results[i][1].object = doc.page_content

def layout_gui(number_of_results, vectorstore):
    from panel import Column, Row
    from panel.pane import Markdown
    from panel.widgets import Button, TextInput
    text_input_query = TextInput(
        value='', placeholder='Enter query here...')
    button_run = Button(name='Run Query')
    rows_results = tuple(
        Row(f"{i}", Markdown('', width=640))
        for i in range(number_of_results))
    button_run.on_click(
        lambda event: run_query(
            event, text_input_query, rows_results, vectorstore) )
    dashboard = Column(
        text_input_query,
        button_run,
        *rows_results)
    return dashboard


def provide_credentials( ):
    import tomli as tomllib
    with open(
        '.local/configuration/credentials.toml', 'rb'
    ) as credentials_file: credentials = tomllib.load(credentials_file)
    return dict(
        openai_api_key = credentials['openai']['token'],
        openai_organization = credentials['openai']['organization'] )

def main():
    import openai
    openai_credentials = provide_credentials( )
    openai.api_key = openai_credentials[ 'openai_api_key' ]
    openai.organization = openai_credentials[ 'openai_organization' ]
    vectorstore = load_vectorstore()
    dashboard = layout_gui(number_of_results=5, vectorstore=vectorstore)
    pn.serve(dashboard, start=True)

if __name__ == "__main__":
    main()
