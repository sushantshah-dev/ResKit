from src.app import create_app
import os, dotenv
dotenv.load_dotenv()

app = create_app()

if __name__ == '__main__':
    app.run(debug=os.getenv('PRODUCTION', 'True') == 'False')
