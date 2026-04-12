"""
Investment Club Management APIs
Handles club creation, joining, member management, and data sharing.
"""

from flask import request, jsonify
from flask_restful import Resource
from applications.database import db
## Model imports moved inside methods to avoid circular import issues
from flask_security import auth_token_required, current_user
import secrets
import datetime


class CreateClubResource(Resource):
    """Create a new investment club"""
    
    @auth_token_required
    def post(self):
        from applications.models import InvestmentClub, ClubMember, ClubSharing
        """Create a new investment club"""
        try:
            data = request.get_json()
            
            if not data or not data.get('club_name'):
                return {'success': False, 'error': 'Club name is required'}, 400
            
            # Generate unique join code
            join_code = f"CLUB-{secrets.token_hex(3).upper()}"
            
            # Create club
            club = InvestmentClub(
                club_name=data['club_name'],
                join_code=join_code,
                created_by=current_user.id
            )
            
            db.session.add(club)
            db.session.flush()  # Get the club ID
            
            # Add creator as admin member
            admin_member = ClubMember(
                user_id=current_user.id,
                club_id=club.id,
                role='admin'
            )
            db.session.add(admin_member)
            
            # Set default sharing preferences for creator
            sharing = ClubSharing(
                user_id=current_user.id,
                club_id=club.id,
                share_portfolio_value=True,
                share_holdings_list=True,
                share_performance=True
            )
            db.session.add(sharing)
            
            db.session.commit()
            
            return {
                'success': True,
                'club': {
                    'id': club.id,
                    'club_name': club.club_name,
                    'join_code': join_code
                },
                'message': 'Investment club created successfully'
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}, 500


class JoinClubResource(Resource):
    """Join an existing investment club"""
    
    @auth_token_required
    def post(self):
        from applications.models import InvestmentClub, ClubMember, ClubSharing
        """Join an existing investment club using join code"""
        try:
            data = request.get_json()
            
            if not data or not data.get('join_code'):
                return {'success': False, 'error': 'Join code is required'}, 400
            
            join_code = data.get('join_code').strip().upper()
            
            # Find club by join code
            club = InvestmentClub.query.filter_by(join_code=join_code).first()
            if not club:
                return {'success': False, 'error': 'Invalid join code'}, 404
            
            # Check if already a member
            existing_member = ClubMember.query.filter_by(
                user_id=current_user.id, 
                club_id=club.id
            ).first()
            
            if existing_member:
                return {'success': False, 'error': 'Already a member of this club'}, 400
            
            # Add as member
            member = ClubMember(
                user_id=current_user.id,
                club_id=club.id,
                role='member'
            )
            db.session.add(member)
            
            # Set default sharing preferences (private by default)
            sharing = ClubSharing(
                user_id=current_user.id,
                club_id=club.id,
                share_portfolio_value=False,
                share_holdings_list=False,
                share_performance=False
            )
            db.session.add(sharing)
            
            db.session.commit()
            
            return {
                'success': True,
                'club': {
                    'id': club.id,
                    'club_name': club.club_name,
                    'join_code': club.join_code
                },
                'message': f'Joined {club.club_name} successfully'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}, 500


class MyClubsResource(Resource):
    """Get all clubs the current user is member of"""
    
    @auth_token_required
    def get(self):
        from applications.models import InvestmentClub, ClubMember
        """Retrieve all clubs for current user"""
        try:
            club_memberships = ClubMember.query.filter_by(user_id=current_user.id).all()
            
            clubs_data = []
            for member in club_memberships:
                club = InvestmentClub.query.get(member.club_id)
                if club:
                    total_members = ClubMember.query.filter_by(club_id=club.id).count()
                    
                    clubs_data.append({
                        'id': club.id,
                        'club_name': club.club_name,
                        'join_code': club.join_code,
                        'role': member.role,
                        'total_members': total_members,
                        'joined_at': member.joined_at.isoformat()
                    })
            
            return {
                'success': True,
                'clubs': clubs_data,
                'total_clubs': len(clubs_data)
            }, 200
            
        except Exception as e:
            return {'success': False, 'error': str(e)}, 500


class ClubDashboardResource(Resource):
    """Get club dashboard with aggregated member data"""
    
    @auth_token_required
    def get(self, club_id):
        from applications.models import InvestmentClub, ClubMember, ClubSharing, User, PortfolioHolding
        """Retrieve club dashboard data - FIXED to show actual shared data"""
        try:
            # Verify user is member of this club
            membership = ClubMember.query.filter_by(
                user_id=current_user.id, 
                club_id=club_id
            ).first()
            
            if not membership:
                return {'success': False, 'error': 'Not a member of this club'}, 403
            
            club = InvestmentClub.query.get(club_id)
            if not club:
                return {'success': False, 'error': 'Club not found'}, 404
            
            # Get all members with their sharing preferences
            members = ClubMember.query.filter_by(club_id=club_id).all()
            
            members_data = []
            total_net_worth = 0
            all_holdings = {}
            visible_members_count = 0
            
            for member in members:
                user = User.query.get(member.user_id)
                sharing = ClubSharing.query.filter_by(
                    user_id=member.user_id, 
                    club_id=club_id
                ).first()
                
                # Always include member, but with conditional data
                member_data = {
                    'user_id': user.id,
                    'username': user.username,
                    'role': member.role,
                    'sharing': {
                        'share_portfolio_value': sharing.share_portfolio_value if sharing else False,
                        'share_holdings_list': sharing.share_holdings_list if sharing else False,
                        'share_performance': sharing.share_performance if sharing else False
                    },
                    'portfolio_value': 0,
                    'top_holdings': [],
                    'performance': 0
                }
                
                # Get user's portfolio data
                holdings = PortfolioHolding.query.filter_by(user_id=member.user_id).all()
                
                if holdings and sharing:
                    total_invested = sum(h.quantity * h.purchase_price for h in holdings)
                    
                    # FIXED: Only include data that user has chosen to share
                    if sharing.share_portfolio_value:
                        member_data['portfolio_value'] = round(total_invested, 2)
                        total_net_worth += total_invested
                    
                    if sharing.share_holdings_list:
                        # Get top holdings sorted by total value
                        holdings_list = [
                            {
                                'symbol': h.symbol,
                                'quantity': h.quantity,
                                'price': round(h.purchase_price, 2),
                                'value': round(h.quantity * h.purchase_price, 2)
                            }
                            for h in sorted(holdings, key=lambda x: x.quantity * x.purchase_price, reverse=True)[:5]
                        ]
                        member_data['top_holdings'] = holdings_list
                        
                        # Track holdings for common analysis
                        for h in holdings:
                            if h.symbol not in all_holdings:
                                all_holdings[h.symbol] = 0
                            all_holdings[h.symbol] += 1
                    
                    if sharing.share_performance:
                        # For now, performance is 0 since we don't have current prices
                        # In production, fetch current price from yfinance
                        member_data['performance'] = 0.0
                
                # Count members sharing at least something
                if (sharing and (sharing.share_portfolio_value or sharing.share_holdings_list or sharing.share_performance)):
                    visible_members_count += 1
                
                members_data.append(member_data)
            
            # Find common holdings (held by multiple members who shared)
            common_holdings = [
                stock for stock, count in all_holdings.items() if count > 1
            ]
            common_holdings = sorted(
                common_holdings, 
                key=lambda x: all_holdings[x], 
                reverse=True
            )[:5]
            
            return {
                'success': True,
                'club': {
                    'id': club.id,
                    'name': club.club_name,
                    'join_code': club.join_code,
                    'created_by': club.created_by,
                    'created_at': club.created_at.isoformat(),
                    'total_members': len(members)
                },
                'dashboard': {
                    'total_members': len(members_data),
                    'visible_members_count': visible_members_count,
                    'total_net_worth': round(total_net_worth, 2),
                    'common_holdings': common_holdings,
                    'members': members_data
                }
            }, 200
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}, 500


class ClubSharingResource(Resource):
    """Update sharing preferences for a club member"""
    
    @auth_token_required
    def post(self):
        from applications.models import ClubMember, ClubSharing
        """Update sharing preferences"""
        try:
            data = request.get_json()
            club_id = data.get('club_id')
            
            if not club_id:
                return {'success': False, 'error': 'Club ID is required'}, 400
            
            # Verify user is member of this club
            membership = ClubMember.query.filter_by(
                user_id=current_user.id, 
                club_id=club_id
            ).first()
            
            if not membership:
                return {'success': False, 'error': 'Not a member of this club'}, 403
            
            # Get or create sharing settings
            sharing = ClubSharing.query.filter_by(
                user_id=current_user.id,
                club_id=club_id
            ).first()
            
            if not sharing:
                return {'success': False, 'error': 'Club membership not found'}, 404
            
            # Update sharing preferences
            if 'share_portfolio_value' in data:
                sharing.share_portfolio_value = bool(data['share_portfolio_value'])
            if 'share_holdings_list' in data:
                sharing.share_holdings_list = bool(data['share_holdings_list'])
            if 'share_performance' in data:
                sharing.share_performance = bool(data['share_performance'])
            
            sharing.updated_at = datetime.datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Sharing preferences updated successfully'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}, 500
    
    @auth_token_required
    def get(self, club_id):
        from applications.models import ClubSharing
        """Get current sharing preferences"""
        try:
            sharing = ClubSharing.query.filter_by(
                user_id=current_user.id,
                club_id=club_id
            ).first()
            
            if not sharing:
                return {'success': False, 'error': 'No sharing preferences found'}, 404
            
            
            return {
                'success': True,
                'sharing': sharing.to_dict()
            }, 200
            
        except Exception as e:
            return {'success': False, 'error': str(e)}, 500


class LeaveClubResource(Resource):
    """Leave an investment club"""
    
    @auth_token_required
    def post(self):
        """Leave a club"""
        from applications.models import ClubMember, ClubSharing, InvestmentClub
        try:
            data = request.get_json()
            club_id = data.get('club_id')
            
            if not club_id:
                return {'success': False, 'error': 'Club ID is required'}, 400
            
            # Verify club exists
            club = InvestmentClub.query.get(club_id)
            if not club:
                return {'success': False, 'error': 'Club not found'}, 404
            
            # Find membership
            membership = ClubMember.query.filter_by(
                user_id=current_user.id,
                club_id=club_id
            ).first()
            
            if not membership:
                return {'success': False, 'error': 'Not a member of this club'}, 404
            
            # Delete sharing preferences first (due to foreign key)
            sharing = ClubSharing.query.filter_by(
                user_id=current_user.id,
                club_id=club_id
            ).first()
            
            if sharing:
                db.session.delete(sharing)
                db.session.flush()  # Flush to ensure deletion before next operation
            
            # Delete membership
            db.session.delete(membership)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Left club successfully'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            print(f"Error in LeaveClubResource: {str(e)}")
            return {'success': False, 'error': str(e)}, 500
