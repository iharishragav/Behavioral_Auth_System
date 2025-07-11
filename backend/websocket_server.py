import asyncio
import websockets
import json
import logging
from ml.behavioral_analyzer import BehavioralAnalyzer
from datetime import datetime

class BehavioralWebSocketServer:
    def __init__(self):
        self.analyzer = BehavioralAnalyzer()
        # Ensure models directory exists
        import os
        if not os.path.exists('models'):
            os.makedirs('models')
        self.analyzer.load_models()
        self.connected_clients = set()
        self.user_sessions = {}
        
        if not self.analyzer.is_trained:
            print("Models not found or not trained. Training with dummy data...")
            self._train_initial_models()

    def _train_initial_models(self):
        # Generate some dummy data for initial training
        dummy_data = []
        for i in range(5):
            dummy_keystroke = [
                {'type': 'keydown', 'keyCode': 65, 'key': 'a', 'timestamp': 100 + i * 10},
                {'type': 'keyup', 'keyCode': 65, 'key': 'a', 'timestamp': 150 + i * 10, 'dwellTime': 50},
                {'type': 'keydown', 'keyCode': 66, 'key': 'b', 'timestamp': 200 + i * 10},
                {'type': 'keyup', 'keyCode': 66, 'key': 'b', 'timestamp': 250 + i * 10, 'dwellTime': 50},
            ]
            dummy_mouse = [
                {'type': 'mousemove', 'x': 100 + i, 'y': 100 + i, 'timestamp': 100 + i * 5},
                {'type': 'mousemove', 'x': 110 + i, 'y': 110 + i, 'timestamp': 110 + i * 5},
                {'type': 'click', 'x': 110 + i, 'y': 110 + i, 'button': 0, 'timestamp': 120 + i * 5},
            ]
            dummy_data.append({
                'user_id': f'user_{i}',
                'behavioral_data': {
                    'keystrokeData': dummy_keystroke,
                    'mouseData': dummy_mouse
                }
            })
        
        self.analyzer.train_global_model(dummy_data)
        print("Initial models trained and saved.")

    async def register_client(self, websocket, path):
        """Register new client connection"""
        self.connected_clients.add(websocket)
        print(f"Client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.discard(websocket)
            print(f"Client disconnected: {websocket.remote_address}")
    
    async def process_message(self, websocket, message):
        """Process incoming behavioral data"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'behavioral_data':
                await self.handle_behavioral_data(websocket, data)
            elif message_type == 'user_authentication':
                await self.handle_user_authentication(websocket, data)
            elif message_type == 'feedback':
                await self.handle_feedback(websocket, data)
                
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON format received: {message}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logging.error(f"Error processing message: {e}", exc_info=True)
            await websocket.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_behavioral_data(self, websocket, data):
        """Handle incoming behavioral data"""
        user_id = data.get('userId')
        session_id = data.get('sessionId')
        keystroke_data = data.get('keystrokeData', [])
        mouse_data = data.get('mouseData', [])
        
        # Analyze behavioral data
        risk_score = self.analyzer.analyze_real_time(
            keystroke_data, mouse_data, user_id
        )
        
        # Store session information
        self.user_sessions[session_id] = {
            'user_id': user_id,
            'websocket': websocket,
            'last_activity': datetime.now(),
            'risk_score': risk_score
        }
        
        # Send response
        response = {
            'type': 'analysis_result',
            'sessionId': session_id,
            'riskScore': risk_score,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send alert if high risk
        if risk_score > 0.7:
            response['alert'] = {
                'level': 'HIGH',
                'message': 'Unusual behavioral patterns detected',
                'recommended_action': 'Require additional authentication'
            }
        elif risk_score > 0.5:
            response['alert'] = {
                'level': 'MEDIUM',
                'message': 'Behavioral patterns slightly deviate from norm'
            }
            
        await websocket.send(json.dumps(response))

    async def handle_user_authentication(self, websocket, data):
        """Handle user authentication events"""
        user_id = data.get('userId')
        session_id = data.get('sessionId')
        logging.info(f"User authentication received: userId={user_id}, sessionId={session_id}")
        
        # Create a new user profile if one doesn't exist
        if user_id not in self.analyzer.user_profiles:
            self.analyzer.create_user_profile(user_id, {
                'keystrokeData': [],
                'mouseData': []
            })
            
        await websocket.send(json.dumps({
            'type': 'authentication_success',
            'userId': user_id
        }))

    async def handle_feedback(self, websocket, data):
        """Handle feedback from the user"""
        user_id = data.get('userId')
        session_id = data.get('sessionId')
        feedback = data.get('feedback')
        behavioral_data = data.get('behavioralData')
        
        # Update user profile based on feedback
        self.analyzer.update_user_profile(user_id, behavioral_data, feedback)
        
        await websocket.send(json.dumps({
            'type': 'feedback_received',
            'message': 'User profile updated'
        }))

async def main():
    server = BehavioralWebSocketServer()

    async with websockets.serve(server.register_client, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())