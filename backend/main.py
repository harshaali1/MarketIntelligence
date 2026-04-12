from flask import Flask
from flask_restful import Api
from flask_security import Security, SQLAlchemySessionUserDatastore
from flask_cors import CORS # Import CORS
from sqlalchemy import text
import os

# Import configurations, db instance, models, datastore, and initialization function
from applications.config import Config
from applications.database import db
from applications.models import User, Role # Ensure both are defined in models.py
from applications.user_datastore import user_datastore # Ensure this is correctly initialized
from create_initial_data import create_data
from applications.stock_7_14 import Predict
from applications.monte_carlo import *
from applications.bullish_berish import *
from applications.portfolio_apis import *
from applications.candle_stick import *

from applications.Graphs_api import *
from applications.ai_chatbot import *
from applications.investment_goals import InvestmentGoalListResource, InvestmentGoalResource
from applications.investment_clubs_apis import (
    CreateClubResource, JoinClubResource, MyClubsResource, 
    ClubDashboardResource, ClubSharingResource, LeaveClubResource
)
from applications.technical_analysis import (
    RSIIndicator, MACDIndicator, BollingerBands, TechnicalSignalCombined
)
# Import API Resource classes
from applications.auth_apis import *

# --- App Factory ---
def create_app():
    """Creates and configures the Flask application using the factory pattern."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config) # Load configuration

    # Initialize extensions that don't depend on others first
    db.init_app(app) # Initialize SQLAlchemy

    # --- ADJUSTED INITIALIZATION ORDER ---
    # 1. Initialize Flask-Restful Api FIRST
    api = Api(app, prefix='/api/v1')
    print("Flask-Restful Api initialized.")

    # 2. Initialize Flask-CORS AFTER Api, applying to the app
    CORS(app, resources={r"/api/*": {
    "origins": [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173"
    ],
    "supports_credentials": True,
    "expose_headers": ["Content-Type", "Authorization"],
    "allow_headers": [
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Auth-Token",
        "X-Requested-With",
        "user-id",
        "Authentication-Token"  # <-- Flask-Security token header
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
}})

    # --- End Adjustment ---

    # 3. Initialize Flask-Security (AFTER db.init_app)
    security = Security(app, user_datastore)
    print("Flask-Security initialized.")

    # Register API Endpoints with Flask-Restful under the /api/v1 prefix
    api.add_resource(Registration, '/signup')    # Accessible at /api/v1/signup
    api.add_resource(Login, '/login')            # Accessible at /api/v1/login
    api.add_resource(Logout, '/logout')          # Accessible at /api/v1/logout
    api.add_resource(ValidUser, '/valid_user')   # Accessible at /api/v1/valid_user
    api.add_resource(WatchlistCheck, '/has_watchlist/<int:user_id>')
    api.add_resource(UserWatchlist, '/watchlist/<int:user_id>')
    api.add_resource(StockAnalyzer, '/analyze')
    api.add_resource(WatchlistItemDeletion, '/watchlist/<int:item_id>')
    api.add_resource(AddToWatchlist, '/watchlist/add')
    
    
    #mlp apis
    api.add_resource(Predict,'/predict')  #/api/v1/predict
    api.add_resource(MonteCarlo, "/montecarlo")
    api.add_resource(TechnicalSignal, "/technical_signal")
    
    #charts api
    api.add_resource(PriceChartAPI, "/chart/price")
    api.add_resource(VolumeChartAPI, "/chart/volume")
    api.add_resource(DMAChartAPI,'/chart/dma')
    api.add_resource(CandleData, "/chart/candle/<string:symbol>")
    #/api/v1/chart/price
    #/api/v1/chart/volume
    
     #protfolio apis
    
    api.add_resource(AddPortfolio, '/portfolio/add')  # POST to add stock
    api.add_resource(PortfolioDashboard, '/portfolio/dashboard/<int:user_id>')  # GET dashboard with stats
    api.add_resource(UpdatePortfolio, '/portfolio/update/<int:holding_id>')  # PUT to update holding
    api.add_resource(DeletePortfolio, '/portfolio/<int:holding_id>')  # DELETE specific holding
    api.add_resource(GetPortfolio, '/portfolio/<int:user_id>')  # GET user's holdings
    
    # Investment Goals APIs
    api.add_resource(InvestmentGoalListResource, '/goals')  # GET all goals, POST new goal
    api.add_resource(InvestmentGoalResource, '/goals/<int:goal_id>')  # GET, PUT, DELETE specific goal
    
    #AI apis
    
    api.add_resource(AIChatbot, '/ai/chat')
    api.add_resource(AIStockAnalyzer, '/ai/analyze-stock')
    api.add_resource(AIPortfolioAdvisor, '/ai/portfolio-advice')
    
    # Investment Club APIs
    api.add_resource(CreateClubResource, '/club/create')
    api.add_resource(JoinClubResource, '/club/join')
    api.add_resource(MyClubsResource, '/club/my-clubs')
    api.add_resource(ClubDashboardResource, '/club/dashboard/<int:club_id>')
    api.add_resource(ClubSharingResource, '/club/sharing')
    api.add_resource(LeaveClubResource, '/club/leave')
    
    # Technical Analysis APIs (RSI, MACD, Bollinger Bands)
    api.add_resource(RSIIndicator, '/technical/rsi/<string:symbol>')
    api.add_resource(MACDIndicator, '/technical/macd/<string:symbol>')
    api.add_resource(BollingerBands, '/technical/bollinger/<string:symbol>')
    api.add_resource(TechnicalSignalCombined, '/technical/signal/<string:symbol>')
    
    print("API resources registered under /api/v1 prefix.")

    return app, api # Return the configured app and api instances

# --- App Creation ---
app, api = create_app()

# --- Database File Path Calculation ---
instance_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'applications', 'instance')
db_filename = 'finance_app.sqlite3' # Ensure this filename matches config.py
db_path = os.path.join(instance_folder, db_filename)

# --- Main Execution Block (Runs when script is executed directly) ---
if __name__ == '__main__':

    # --- Conditional Database Setup ---
    if not os.path.exists(db_path):
        print(f"Database file not found at '{db_path}'. Initializing database...")
        with app.app_context():
            print("Entering application context for initial DB setup...")
            try:
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                print("Instance folder checked/created.")

                if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
                    db.session.execute(text('PRAGMA foreign_keys=ON'))
                    print("SQLite Foreign Key support enabled via PRAGMA.")

                print("Executing db.create_all()...")
                db.create_all()
                print("Database tables checked/created.")

                print("Executing create_data function...")
                create_data(app, db, user_datastore)
                print("Initial data creation process finished.")

            except Exception as e:
                print(f"ERROR during initial DB setup: {e}")
                db.session.rollback()
            finally:
                print("Exiting application context for initial DB setup.")
    else:
        print(f"Database file already exists at '{db_path}'. Skipping initialization.")
    # --- End Conditional DB Setup ---

    # --- Start the Flask Development Server ---
    print("Starting Flask development server...")
    app.run(debug=True, host='0.0.0.0', port=5001)

