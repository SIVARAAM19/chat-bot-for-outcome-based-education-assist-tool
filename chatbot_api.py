from flask import Flask, request, jsonify
import logging
from actions.utils.query_router import route_query


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/query', methods=['POST'])
def process_query():
    """Process a query and return the response"""
    query_text = request.form.get('query', '')
    
    if not query_text:
        return jsonify({
            'success': False,
            'message': 'No query provided'
        })
    
    logger.info(f"Received query: {query_text}")
    
   
    result = route_query(query_text)
    
   
    return jsonify({
        'success': result.get('success', False),
        'message': result.get('message', 'Sorry, I could not process your request.'),
        'query_type': result.get('query_type', 'unknown')
    })

if __name__ == '__main__':
    logger.info("Starting chatbot API server...")
    app.run(debug=True, port=5005) 