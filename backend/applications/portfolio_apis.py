from flask_restful import Resource, reqparse
from flask import jsonify, request, make_response
from flask_security import hash_password, utils, auth_token_required, current_user
from applications.user_datastore import user_datastore
from applications.database import db
from applications.models import User, PortfolioHolding, PortfolioSnapshot
from sqlalchemy.sql import exists
from sqlalchemy.exc import IntegrityError
import uuid
import pandas as pd
import yfinance as yf
from flask_security import auth_token_required, current_user
from datetime import datetime, timedelta

# --- PORTFOLIO CRUD ENDPOINTS ---

class AddPortfolio(Resource):
    """POST /api/v1/portfolio/add - Add stock to portfolio"""
    def post(self):
        try:
            data = request.get_json()
            
            # Get user_id from request body (frontend sends it)
            user_id = data.get('user_id')
            if not user_id:
                return make_response(jsonify({'message': 'User ID is required'}), 400)
            
            # Verify user exists in database
            user = User.query.get(user_id)
            if not user:
                return make_response(jsonify({'message': 'User not found'}), 404)
            
            # Validate required fields
            symbol = data.get('symbol', '').upper().strip()
            quantity = data.get('quantity')
            purchase_price = data.get('purchase_price')
            purchase_date_str = data.get('purchase_date')
            notes = data.get('notes', '')
            
            if not symbol:
                return make_response(jsonify({'message': 'Stock symbol is required'}), 400)
            
            if not quantity or float(quantity) <= 0:
                return make_response(jsonify({'message': 'Quantity must be positive'}), 400)
            
            if not purchase_price or float(purchase_price) <= 0:
                return make_response(jsonify({'message': 'Purchase price must be positive'}), 400)
            
            if not purchase_date_str:
                return make_response(jsonify({'message': 'Purchase date is required'}), 400)
            
            # Parse and validate date
            try:
                purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d')
                if purchase_date > datetime.now():
                    return make_response(jsonify({'message': 'Purchase date cannot be in future'}), 400)
            except ValueError:
                return make_response(jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400)
            
            # Validate stock exists
            try:
                yf_symbol = f"{symbol}.NS" if '.' not in symbol else symbol
                ticker = yf.Ticker(yf_symbol)
                info = ticker.info
                
                if not info.get('currentPrice') and not info.get('regularMarketPrice'):
                    return make_response(jsonify({'message': f'Stock symbol {symbol} not found'}), 404)
                
            except Exception as e:
                return make_response(jsonify({'message': f'Unable to validate stock: {str(e)}'}), 400)
            
            # Create holding
            holding = PortfolioHolding(
                user_id=user_id,
                symbol=symbol,
                quantity=float(quantity),
                purchase_price=float(purchase_price),
                purchase_date=purchase_date,
                notes=notes.strip() if notes else ""
            )
            
            db.session.add(holding)
            db.session.commit()
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or float(purchase_price)
            
            return make_response(jsonify({
                'message': 'Stock added to portfolio successfully',
                'holding': holding.to_dict(current_price=current_price)
            }), 201)
            
        except ValueError as ve:
            return make_response(jsonify({'message': f'Invalid input: {str(ve)}'}), 400)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'message': f'Error adding holding: {str(e)}'}), 500)


class GetPortfolio(Resource):
    """GET /api/v1/portfolio/<user_id> - Get all portfolio holdings"""
    def get(self, user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return make_response(jsonify({'message': 'User not found'}), 404)
            
            holdings = PortfolioHolding.query.filter_by(user_id=user_id).all()
            
            if not holdings:
                return make_response(jsonify({
                    'holdings': [],
                    'summary': {
                        'total_value': 0,
                        'total_invested': 0,
                        'total_gain_loss': 0,
                        'total_gain_loss_percent': 0,
                        'holdings_count': 0
                    }
                }), 200)
            
            # Fetch current prices
            holdings_data = []
            for holding in holdings:
                try:
                    yf_symbol = f"{holding.symbol}.NS" if '.' not in holding.symbol else holding.symbol
                    ticker = yf.Ticker(yf_symbol)
                    # Use history() for real-time price, not cached .info
                    history = ticker.history(period='5d')
                    if not history.empty:
                        current_price = history['Close'].iloc[-1]
                    else:
                        current_price = holding.purchase_price
                except Exception as e:
                    print(f"[PRICE_FETCH_ERROR] {holding.symbol}: {e}")
                    current_price = holding.purchase_price
                
                holdings_data.append(holding.to_dict(current_price=current_price))
            
            # Calculate summary
            total_value = sum(h['current_value'] for h in holdings_data)
            total_invested = sum(h['total_invested'] for h in holdings_data)
            total_gain_loss = total_value - total_invested
            total_gain_loss_percent = (total_gain_loss / total_invested * 100) if total_invested != 0 else 0
            
            return make_response(jsonify({
                'holdings': holdings_data,
                'summary': {
                    'total_value': round(total_value, 2),
                    'total_invested': round(total_invested, 2),
                    'total_gain_loss': round(total_gain_loss, 2),
                    'total_gain_loss_percent': round(total_gain_loss_percent, 2),
                    'holdings_count': len(holdings_data)
                }
            }), 200)
        except Exception as e:
            return make_response(jsonify({'message': f'Error retrieving holdings: {str(e)}'}), 500)


class UpdatePortfolio(Resource):
    """PUT /api/v1/portfolio/update/<holding_id> - Update portfolio holding"""
    def put(self, holding_id):
        try:
            data = request.get_json()
            
            # Get user_id from request body
            user_id = data.get('user_id')
            if not user_id:
                return make_response(jsonify({'message': 'User ID is required'}), 400)
            
            # Verify user exists
            user = User.query.get(user_id)
            if not user:
                return make_response(jsonify({'message': 'User not found'}), 404)
            
            # Get holding and verify it belongs to user
            holding = PortfolioHolding.query.filter_by(id=holding_id, user_id=user_id).first()
            if not holding:
                return make_response(jsonify({'message': 'Holding not found'}), 404)
            
            # Update fields
            if 'quantity' in data:
                quantity = float(data['quantity'])
                if quantity <= 0:
                    return make_response(jsonify({'message': 'Quantity must be positive'}), 400)
                holding.quantity = quantity
            
            if 'purchase_price' in data:
                purchase_price = float(data['purchase_price'])
                if purchase_price <= 0:
                    return make_response(jsonify({'message': 'Purchase price must be positive'}), 400)
                holding.purchase_price = purchase_price
            
            if 'purchase_date' in data:
                try:
                    purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d')
                    if purchase_date > datetime.now():
                        return make_response(jsonify({'message': 'Date cannot be in future'}), 400)
                    holding.purchase_date = purchase_date
                except ValueError:
                    return make_response(jsonify({'message': 'Invalid date format'}), 400)
            
            if 'notes' in data:
                holding.notes = data['notes'].strip() if data['notes'] else None
            
            db.session.commit()
            
            # Get current price
            try:
                yf_symbol = f"{holding.symbol}.NS" if '.' not in holding.symbol else holding.symbol
                ticker = yf.Ticker(yf_symbol)
                info = ticker.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice') or holding.purchase_price
            except:
                current_price = holding.purchase_price
            
            return make_response(jsonify({
                'message': 'Holding updated successfully',
                'holding': holding.to_dict(current_price=current_price)
            }), 200)
            
        except ValueError as ve:
            return make_response(jsonify({'message': f'Invalid input: {str(ve)}'}), 400)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'message': f'Error updating holding: {str(e)}'}), 500)


class DeletePortfolio(Resource):
    """DELETE /api/v1/portfolio/<holding_id> - Remove holding from portfolio"""
    def delete(self, holding_id):
        try:
            data = request.get_json() or {}
            
            # Get user_id from request body
            user_id = data.get('user_id')
            if not user_id:
                return make_response(jsonify({'message': 'User ID is required'}), 400)
            
            # Verify user exists
            user = User.query.get(user_id)
            if not user:
                return make_response(jsonify({'message': 'User not found'}), 404)
            
            # Get holding and verify it belongs to user
            holding = PortfolioHolding.query.filter_by(id=holding_id, user_id=user_id).first()
            
            if not holding:
                return make_response(jsonify({'message': 'Holding not found'}), 404)
            
            symbol = holding.symbol
            db.session.delete(holding)
            db.session.commit()
            
            return make_response(jsonify({
                'message': f'{symbol} removed from portfolio successfully'
            }), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'message': f'Error deleting holding: {str(e)}'}), 500)


class PortfolioDashboard(Resource):
    """GET /api/v1/portfolio/dashboard/<user_id> - Portfolio dashboard with health score & doughnut chart data"""
    def get(self, user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return make_response(jsonify({'message': 'User not found'}), 404)
            
            holdings = PortfolioHolding.query.filter_by(user_id=user_id).all()
            
            if not holdings:
                return make_response(jsonify({
                    'summary': {
                        'total_value': 0,
                        'total_invested': 0,
                        'total_gain_loss': 0,
                        'total_gain_loss_percent': 0,
                        'holdings_count': 0
                    },
                    'health_score': 0,
                    'health_status': 'No Portfolio',
                    'doughnut_data': {
                        'labels': [],
                        'data': [],
                        'percentages': []
                    },
                    'top_performer': None,
                    'worst_performer': None
                }), 200)
            
            # Fetch current prices and build holdings data
            holdings_data = []
            for holding in holdings:
                try:
                    yf_symbol = f"{holding.symbol}.NS" if '.' not in holding.symbol else holding.symbol
                    ticker = yf.Ticker(yf_symbol)
                    # Use history() for real-time price, not cached .info
                    history = ticker.history(period='5d')
                    if not history.empty:
                        current_price = history['Close'].iloc[-1]
                    else:
                        current_price = holding.purchase_price
                except Exception as e:
                    print(f"[PRICE_FETCH_ERROR] {holding.symbol}: {e}")
                    current_price = holding.purchase_price
                
                holding_dict = holding.to_dict(current_price=current_price)
                holding_dict['symbol'] = holding.symbol
                holdings_data.append(holding_dict)
            
            # Calculate summary
            total_value = sum(h['current_value'] for h in holdings_data)
            total_invested = sum(h['total_invested'] for h in holdings_data)
            total_gain_loss = total_value - total_invested
            total_gain_loss_percent = (total_gain_loss / total_invested * 100) if total_invested != 0 else 0
            
            # Calculate health score (1-10)
            health_score = calculate_health_score(holdings_data, total_invested)
            
            # Determine health status
            if health_score >= 8:
                health_status = 'Excellent'
            elif health_score >= 6:
                health_status = 'Good'
            elif health_score >= 4:
                health_status = 'Fair'
            else:
                health_status = 'Poor'
            
            # Build doughnut chart data (Stock-wise allocation & percentages)
            doughnut_labels = []
            doughnut_values = []
            doughnut_percentages = []
            
            for holding in holdings_data:
                doughnut_labels.append(holding['symbol'])
                doughnut_values.append(holding['total_invested'])
                percentage = (holding['total_invested'] / total_invested * 100) if total_invested > 0 else 0
                doughnut_percentages.append(round(percentage, 2))
            
            # Find top and worst performers
            top_performer = max(holdings_data, key=lambda x: x.get('gain_loss_percent', 0), default=None)
            worst_performer = min(holdings_data, key=lambda x: x.get('gain_loss_percent', 0), default=None)
            
            return make_response(jsonify({
                'holdings': holdings_data,
                'summary': {
                    'total_value': round(total_value, 2),
                    'total_invested': round(total_invested, 2),
                    'total_gain_loss': round(total_gain_loss, 2),
                    'total_gain_loss_percent': round(total_gain_loss_percent, 2),
                    'holdings_count': len(holdings_data)
                },
                'health_score': health_score,
                'health_status': health_status,
                'doughnut_data': {
                    'labels': doughnut_labels,
                    'invested_amounts': doughnut_values,
                    'percentages': doughnut_percentages
                },
                'top_performer': {
                    'symbol': top_performer['symbol'],
                    'gain_loss_percent': top_performer.get('gain_loss_percent', 0)
                } if top_performer else None,
                'worst_performer': {
                    'symbol': worst_performer['symbol'],
                    'gain_loss_percent': worst_performer.get('gain_loss_percent', 0)
                } if worst_performer else None
            }), 200)
            
        except Exception as e:
            return make_response(jsonify({'message': f'Error retrieving dashboard: {str(e)}'}), 500)


# --- HELPER FUNCTION ---

def calculate_health_score(holdings_data, total_invested):
    """Calculate portfolio health score (1-10)"""
    if not holdings_data or total_invested == 0:
        return 0
    
    score = 10
    
    # Diversification penalty
    if len(holdings_data) < 3:
        score -= 2
    elif len(holdings_data) < 5:
        score -= 1
    
    # Concentration risk penalty
    max_allocation = max((h['total_invested'] / total_invested * 100) for h in holdings_data)
    if max_allocation > 50:
        score -= 3
    elif max_allocation > 40:
        score -= 2
    elif max_allocation > 30:
        score -= 1
    
    # Performance bonus
    total_gain_loss_percent = sum(h.get('gain_loss_percent', 0) for h in holdings_data) / len(holdings_data)
    if total_gain_loss_percent > 10:
        score += 1
    elif total_gain_loss_percent < -5:
        score -= 1
    
    # Ensure score between 1-10
    return max(1, min(10, score))