from flask_restful import Resource, reqparse
from flask import jsonify, request, make_response
from flask_security import auth_token_required, current_user
import google.generativeai as genai
from applications.models import PortfolioHolding, User
from applications.database import db
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # List available models for debugging
    try:
        available_models = genai.list_models()
        print("[DEBUG] Available Gemini models:")
        for model in available_models:
            print(f"  - {model.name}")
    except Exception as e:
        print(f"[DEBUG] Could not list models: {e}")
else:
    print("[WARNING] GEMINI_API_KEY not found in .env file")

# Parser for chatbot messages
chat_parser = reqparse.RequestParser()
chat_parser.add_argument('message', type=str, required=True, help='Message is required', location='json')
chat_parser.add_argument('user_id', type=int, required=True, help='User ID is required', location='json')

# Parser for stock analysis
stock_parser = reqparse.RequestParser()
stock_parser.add_argument('ticker', type=str, required=True, help='Ticker symbol is required', location='json')


class AIChatbot(Resource):
    """POST /api/v1/ai/chat - AI-powered financial chatbot with portfolio context"""
    
    def post(self):
        try:
            args = chat_parser.parse_args()
            user_id = args['user_id']
            user_message = args['message'].strip()
            
            if not user_message:
                return make_response(jsonify({'message': 'Message cannot be empty'}), 400)
            
            # Verify user exists
            user = User.query.get(user_id)
            if not user:
                return make_response(jsonify({'message': 'User not found'}), 404)
            
            if not GEMINI_API_KEY:
                return make_response(jsonify({'message': 'Gemini API key not configured'}), 500)
            
            # Get user's portfolio context
            portfolio_context = self._get_portfolio_context(user_id)
            
            # Build system prompt with portfolio context
            system_prompt = self._build_system_prompt(portfolio_context)
            
            # Get AI response using Gemini
            ai_response = self._get_gemini_response(system_prompt, user_message)
            
            if not ai_response:
                return make_response(jsonify({'message': 'Failed to get AI response'}), 500)
            
            return make_response(jsonify({
                'success': True,
                'user_message': user_message,
                'ai_response': ai_response,
                'portfolio_status': portfolio_context.get('status', 'unknown')
            }), 200)
        
        except Exception as e:
            print(f"[CHATBOT_ERROR]: {e}")
            return make_response(jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500)
    
    def _get_portfolio_context(self, user_id):
        """Fetch user's portfolio data for context"""
        try:
            holdings = PortfolioHolding.query.filter_by(user_id=user_id).all()
            
            if not holdings:
                return {
                    'status': 'empty',
                    'message': 'No portfolio holdings yet',
                    'total_invested': 0,
                    'holdings_count': 0
                }
            
            total_invested = 0
            holdings_list = []
            
            for holding in holdings:
                invested = holding.quantity * holding.purchase_price
                total_invested += invested
                
                holdings_list.append({
                    'symbol': holding.symbol,
                    'quantity': holding.quantity,
                    'purchase_price': holding.purchase_price,
                    'invested_amount': invested,
                    'purchase_date': holding.purchase_date.strftime('%Y-%m-%d') if holding.purchase_date else 'N/A'
                })
            
            return {
                'status': 'active',
                'total_invested': round(total_invested, 2),
                'holdings_count': len(holdings_list),
                'holdings': holdings_list
            }
        
        except Exception as e:
            print(f"[PORTFOLIO_CONTEXT_ERROR]: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'holdings_count': 0
            }
    
    def _build_system_prompt(self, portfolio_context):
        """Build comprehensive system prompt with portfolio context"""
        
        if portfolio_context['status'] == 'empty':
            portfolio_info = """
USER PORTFOLIO STATUS: Empty (No stocks owned yet)
The user is just starting their investment journey. Help them understand investment basics, 
how to build a diversified portfolio, and suggest good beginner stocks for Indian market.
"""
        elif portfolio_context['status'] == 'error':
            portfolio_info = "Could not fetch portfolio data. Provide general investment advice."
        else:
            holdings_str = "\n".join([
                f"  • {h['symbol']}: {h['quantity']} shares @ ₹{h['purchase_price']:.2f} = ₹{h['invested_amount']:.2f} (Bought: {h['purchase_date']})"
                for h in portfolio_context.get('holdings', [])
            ])
            
            portfolio_info = f"""
USER PORTFOLIO STATUS: Active
Current Holdings ({portfolio_context['holdings_count']} stocks):
{holdings_str}

Portfolio Summary:
  • Total Invested: ₹{portfolio_context['total_invested']:,.2f}
  • Holdings Count: {portfolio_context['holdings_count']}
"""
        
        system_prompt = f"""You are an expert financial advisor and investment coach specializing in Indian stock market analysis.

{portfolio_info}

Your Expertise:
- Indian stock market (NSE/BSE)
- Technical and fundamental analysis
- Portfolio diversification and rebalancing
- Risk management and asset allocation
- Stocks, mutual funds, and ETFs
- Market trends and sentiment analysis
- Investment psychology and behavior

Your Role:
1. Provide personalized investment advice based on the user's actual portfolio
2. Analyze stock performance and market trends
3. Suggest portfolio rebalancing strategies when needed
4. Explain investment concepts in simple, understandable terms
5. Help assess risk tolerance and investment goals
6. Provide market insights with Indian market focus
7. Answer specific questions about stocks, sectors, and industries
8. Give actionable recommendations for portfolio improvement

Guidelines for Responses:
- Always consider the user's current holdings and risk profile
- Provide specific, actionable advice with reasoning
- Reference real market data when discussing stocks
- Explain financial concepts clearly without jargon
- Recommend diversification if portfolio is too concentrated in one stock/sector
- Warn about high-risk concentrations (>40% in single stock)
- Be cautious and risk-aware in all recommendations
- Include both opportunities and risks in your analysis
- Ask clarifying questions if needed to better understand user's goals
- Consider time horizons, investment amounts, and risk tolerance

IMPORTANT: You are advising a real investor with real money. Be responsible and thorough."""
        
        return system_prompt
    
    def _get_gemini_response(self, system_prompt, user_message):
        """Get response from Google Gemini API"""
        try:
            if not GEMINI_API_KEY:
                return None
            
            # Use gemini-2.5-flash with correct format
            model = genai.GenerativeModel(
                model_name='models/gemini-2.5-flash',
                system_instruction=system_prompt
            )
            
            response = model.generate_content(user_message)
            return response.text if response and hasattr(response, 'text') else None
        
        except Exception as e:
            print(f"[GEMINI_API_ERROR]: {e}")
            return None


class AIStockAnalyzer(Resource):
    """POST /api/v1/ai/analyze-stock - Analyze specific stock with AI"""
    
    def post(self):
        try:
            args = stock_parser.parse_args()
            ticker = args['ticker'].upper().strip()
            
            if not ticker:
                return make_response(jsonify({'message': 'Ticker symbol is required'}), 400)
            
            if not GEMINI_API_KEY:
                return make_response(jsonify({'message': 'Gemini API key not configured'}), 500)
            
            analysis_prompt = f"""Provide a comprehensive investment analysis for {ticker} stock:

1. **Company Overview**: 
   - What does the company do?
   - Business model and operations

2. **Current Market Position**:
   - Recent price trends
   - Market sentiment
   - Trading volume and liquidity

3. **Financial Metrics**:
   - P/E ratio, Market cap (if available)
   - Key financial indicators
   - Growth prospects

4. **Investment Case**:
   - Why investors might be interested
   - Competitive advantages
   - Growth opportunities

5. **Risks & Concerns**:
   - Key risks to consider
   - Market challenges
   - Sector headwinds

6. **Technical Outlook**:
   - Short-term (1-3 months) outlook
   - Long-term (1+ year) outlook
   - Key support/resistance levels

7. **Recommendation**:
   - Strong Buy / Buy / Hold / Sell
   - Target price (if available)
   - Reasoning

8. **Who Should Consider**:
   - Suitable investor profile
   - Risk tolerance level
   - Investment horizon

Focus on Indian market perspective. Be specific and data-driven where possible."""
            
            model = genai.GenerativeModel(model_name='models/gemini-2.5-flash')
            response = model.generate_content(analysis_prompt)
            
            analysis_text = response.text if response and hasattr(response, 'text') else "Could not generate analysis"
            
            return make_response(jsonify({
                'ticker': ticker,
                'analysis': analysis_text,
                'generated_at': datetime.now().isoformat()
            }), 200)
        
        except Exception as e:
            print(f"[STOCK_ANALYZER_ERROR]: {e}")
            return make_response(jsonify({'message': f'Error analyzing stock: {str(e)}'}), 500)


class AIPortfolioAdvisor(Resource):
    """POST /api/v1/ai/portfolio-advice - Get comprehensive portfolio advice"""
    
    def post(self):
        try:
            # Get user_id from request body instead of relying on current_user
            data = request.get_json()
            user_id = data.get('user_id')
            
            if not user_id:
                return make_response(jsonify({'message': 'User ID is required'}), 400)
            
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return make_response(jsonify({'message': 'Invalid User ID format'}), 400)
            
            # Verify user
            user = User.query.get(user_id)
            if not user:
                return make_response(jsonify({'message': 'User not found'}), 404)
            
            if not GEMINI_API_KEY:
                return make_response(jsonify({'message': 'Gemini API key not configured'}), 500)
            
            # Get portfolio
            holdings = PortfolioHolding.query.filter_by(user_id=user_id).all()
            
            if not holdings:
                return make_response(jsonify({
                    'message': 'No portfolio to analyze',
                    'advice': 'Start building your portfolio by adding stocks you believe in. A diversified portfolio typically includes 5-10 stocks across different sectors.'
                }), 200)
            
            # Calculate portfolio metrics
            total_invested = sum(h.quantity * h.purchase_price for h in holdings)
            holdings_str = "\n".join([
                f"- {h.symbol}: {h.quantity} shares @ ₹{h.purchase_price:.2f} = ₹{h.quantity * h.purchase_price:,.2f}"
                for h in holdings
            ])
            
            advisor_prompt = f"""A user has the following stock portfolio with {len(holdings)} holdings:

{holdings_str}

Total Invested: ₹{total_invested:,.2f}

Please provide comprehensive portfolio advice including:

1. **Portfolio Assessment**:
   - Overall health and composition
   - Strengths and weaknesses
   - Risk level (Aggressive/Moderate/Conservative)

2. **Diversification Analysis**:
   - Is it well-diversified across sectors?
   - Any over-concentration risks?
   - Sector-wise breakdown

3. **Performance Optimization**:
   - Which stocks to hold for long-term?
   - Any underperformers to consider exiting?
   - Opportunities for better growth

4. **Rebalancing Suggestions**:
   - Should portfolio be rebalanced?
   - Stocks to consider adding
   - Stocks to consider reducing

5. **Risk Management**:
   - Portfolio risk profile
   - Hedging strategies if needed
   - Stop-loss recommendations

6. **Tax Efficiency**:
   - Tax-saving strategies (if applicable)
   - Optimal holding periods

7. **Growth Opportunities**:
   - Sector recommendations for future additions
   - Underrated stocks to consider
   - Emerging opportunities

8. **Action Items** (Prioritized):
   - Top 3 immediate recommendations
   - Medium-term goals (3-6 months)
   - Long-term vision (1+ year)

Provide specific, actionable advice tailored to this portfolio."""
            
            model = genai.GenerativeModel(model_name='models/gemini-2.5-flash')
            response = model.generate_content(advisor_prompt)
            
            advice_text = response.text if response and hasattr(response, 'text') else "Could not generate advice"
            
            return make_response(jsonify({
                'user_id': user_id,
                'holdings_count': len(holdings),
                'total_invested': round(total_invested, 2),
                'portfolio_advice': advice_text,
                'generated_at': datetime.now().isoformat()
            }), 200)
        
        except Exception as e:
            print(f"[PORTFOLIO_ADVISOR_ERROR]: {e}")
            return make_response(jsonify({'message': f'Error getting advice: {str(e)}'}), 500)