from flask_restful import Resource, reqparse
from .models import InvestmentGoal, db 
from datetime import datetime

# Parser for POST/PUT (User ID expected in body)
goal_parser = reqparse.RequestParser()
goal_parser.add_argument('user_id', type=int, required=True, help='User ID is required', location='json') # <-- Added user_id
goal_parser.add_argument('goal_name', required=True, help='Goal name is required', location='json')
goal_parser.add_argument('target_amount', type=float, required=True, help='Target amount is required', location='json')
goal_parser.add_argument('target_date', required=True, help='Target date (YYYY-MM-DD) is required', location='json')
# ... (Other arguments)

# Parser for GET (User ID expected in query parameters)
user_id_parser = reqparse.RequestParser()
user_id_parser.add_argument('user_id', type=int, required=True, help='User ID is required in query params', location='args')


class InvestmentGoalListResource(Resource):
    
    def get(self):
        """Fetch all goals for a specific user ID from query parameters."""
        args = user_id_parser.parse_args()
        user_id = args['user_id']
        
        goals = InvestmentGoal.query.filter_by(user_id=user_id).all()
        return [goal.to_dict() for goal in goals], 200

    def post(self):
        """Create a new investment goal, using user_id from the JSON body."""
        args = goal_parser.parse_args()
        user_id = args['user_id'] # Get user_id from JSON payload

        try:
            target_date = datetime.strptime(args['target_date'], '%Y-%m-%d')
        except ValueError:
            return {'message': 'Invalid date format. Use YYYY-MM-DD.'}, 400

        new_goal = InvestmentGoal(
            user_id=user_id,
            goal_name=args['goal_name'],
            target_amount=args['target_amount'],
            target_date=target_date,
            # ... (other field assignments)
        )
        db.session.add(new_goal)
        db.session.commit()
        return new_goal.to_dict(), 201
    
    
# Parser for DELETE (requires user_id in body for security check)
delete_parser = reqparse.RequestParser()
delete_parser.add_argument('user_id', type=int, required=True, help='User ID is required for verification', location='json')


class InvestmentGoalResource(Resource):
    
    # We still need to PUT/DELETE to know the user_id, so GET is less safe here
    def get(self, goal_id):
        """
        Fetch a specific goal by ID.
        Note: The user_id is NOT checked here, which is insecure.
        A query parameter or body check is highly recommended.
        """
        goal = InvestmentGoal.query.filter_by(id=goal_id).first()
        if not goal:
            return {'message': 'Goal not found.'}, 404
        return goal.to_dict(), 200

    def put(self, goal_id):
        """Update an existing goal, requiring user_id for verification."""
        args = goal_parser.parse_args() # Uses the parser with user_id
        user_id = args['user_id']
        
        # CRUCIAL: Filter by BOTH goal ID and user ID
        goal = InvestmentGoal.query.filter_by(id=goal_id, user_id=user_id).first()
        if not goal:
            return {'message': 'Goal not found or access denied.'}, 404

        # ... (update goal fields)
            
        db.session.commit()
        return goal.to_dict(), 200

    def delete(self, goal_id):
        """Delete a goal, requiring user_id for verification."""
        args = delete_parser.parse_args()
        user_id = args['user_id']

        # CRUCIAL: Filter by BOTH goal ID and user ID
        goal = InvestmentGoal.query.filter_by(id=goal_id, user_id=user_id).first()
        if not goal:
            return {'message': 'Goal not found or access denied.'}, 404
        
        db.session.delete(goal)
        db.session.commit()
        return {'message': 'Goal deleted successfully.'}, 204