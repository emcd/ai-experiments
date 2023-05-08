''' Simple GUI built with Panel to support vectorstore and LLM queries. '''


def layout_gui( number_of_results ):
    from panel import Column, Row
    from panel.pane import Markdown
    from panel.widgets import Button, TextInput
    text_input_query = TextInput(
        value = '', placeholder = 'Enter query here...' )
    button_run = Button( name = 'Run Query' )
    rows_results = tuple(
        Row( f"{i}", Markdown( '', width = 640 ) )
        for i in range( number_of_results ) )
    dashboard = Column(
        text_input_query,
        button_run,
        *rows_results )
