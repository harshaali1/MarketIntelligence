"""
Technical Analysis Module - Real Financial Indicators
RSI (Relative Strength Index), MACD, Bollinger Bands
"""

import numpy as np
import pandas as pd
from flask_restful import Resource, reqparse
from flask import jsonify, request, make_response
import yfinance as yf
from datetime import datetime, timedelta

class RSIIndicator(Resource):
    """GET /api/v1/technical/rsi/<symbol> - Calculate RSI (14-period default)"""
    
    def get(self, symbol):
        """
        RSI Formula:
        RS = Average Gain / Average Loss (over 14 periods)
        RSI = 100 - (100 / (1 + RS))
        
        Signal:
        - RSI > 70: Overbought (potential sell)
        - RSI < 30: Oversold (potential buy)
        """
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('period', type=int, default=14, help='RSI period')
            parser.add_argument('days', type=int, default=60, help='Historical days')
            args = parser.parse_args()
            
            # Fetch historical data
            ticker = symbol if '.' in symbol else f"{symbol}.NS"
            data = yf.download(ticker, period=f"{args.days}d", progress=False)
            
            if data.empty:
                return make_response(jsonify({'error': f'No data for {symbol}'}), 404)
            
            # Calculate price changes
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=args.period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=args.period).mean()
            
            # Calculate RS and RSI
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = float(rsi.iloc[-1])
            prev_rsi = float(rsi.iloc[-2]) if len(rsi) > 1 else current_rsi
            
            # Determine signal
            if current_rsi > 70:
                signal = "OVERBOUGHT"
                recommendation = "Potential SELL signal"
            elif current_rsi < 30:
                signal = "OVERSOLD"
                recommendation = "Potential BUY signal"
            else:
                signal = "NEUTRAL"
                recommendation = "Hold position"
            
            return make_response(jsonify({
                'success': True,
                'symbol': symbol,
                'indicator': 'RSI',
                'period': args.period,
                'current_rsi': round(current_rsi, 2),
                'previous_rsi': round(prev_rsi, 2),
                'rsi_change': round(current_rsi - prev_rsi, 2),
                'signal': signal,
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat()
            }), 200)
            
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class MACDIndicator(Resource):
    """GET /api/v1/technical/macd/<symbol> - Calculate MACD"""
    
    def get(self, symbol):
        """
        MACD Formula:
        - MACD Line = 12-period EMA - 26-period EMA
        - Signal Line = 9-period EMA of MACD
        - Histogram = MACD Line - Signal Line
        
        Signal:
        - MACD > Signal: Bullish (uptrend)
        - MACD < Signal: Bearish (downtrend)
        - Positive Histogram: Upward momentum
        """
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('days', type=int, default=90, help='Historical days')
            args = parser.parse_args()
            
            # Fetch historical data
            ticker = symbol if '.' in symbol else f"{symbol}.NS"
            data = yf.download(ticker, period=f"{args.days}d", progress=False)
            
            if data.empty:
                return make_response(jsonify({'error': f'No data for {symbol}'}), 404)
            
            # Calculate EMAs
            ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
            
            # Calculate MACD
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            histogram = macd_line - signal_line
            
            current_macd = float(macd_line.iloc[-1])
            current_signal = float(signal_line.iloc[-1])
            current_histogram = float(histogram.iloc[-1])
            
            # Determine trend
            if current_macd > current_signal:
                signal = "BULLISH"
                recommendation = "Uptrend - Consider BUY"
            else:
                signal = "BEARISH"
                recommendation = "Downtrend - Consider SELL"
            
            momentum = "POSITIVE" if current_histogram > 0 else "NEGATIVE"
            
            return make_response(jsonify({
                'success': True,
                'symbol': symbol,
                'indicator': 'MACD',
                'macd_line': round(current_macd, 4),
                'signal_line': round(current_signal, 4),
                'histogram': round(current_histogram, 4),
                'trend': signal,
                'momentum': momentum,
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat()
            }), 200)
            
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class BollingerBands(Resource):
    """GET /api/v1/technical/bollinger/<symbol> - Calculate Bollinger Bands"""
    
    def get(self, symbol):
        """
        Bollinger Bands Formula:
        - Middle Band = 20-period SMA
        - Upper Band = Middle + (2 * std deviation)
        - Lower Band = Middle - (2 * std deviation)
        
        Signal:
        - Price > Upper Band: Overbought (potential sell)
        - Price < Lower Band: Oversold (potential buy)
        - Bandwidth: Volatility indicator
        """
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('period', type=int, default=20, help='SMA period')
            parser.add_argument('std_dev', type=float, default=2.0, help='Standard deviations')
            parser.add_argument('days', type=int, default=60, help='Historical days')
            args = parser.parse_args()
            
            # Fetch historical data
            ticker = symbol if '.' in symbol else f"{symbol}.NS"
            data = yf.download(ticker, period=f"{args.days}d", progress=False)
            
            if data.empty:
                return make_response(jsonify({'error': f'No data for {symbol}'}), 404)
            
            # Calculate Bollinger Bands
            sma = data['Close'].rolling(window=args.period).mean()
            std = data['Close'].rolling(window=args.period).std()
            
            upper_band = sma + (std * args.std_dev)
            lower_band = sma - (std * args.std_dev)
            
            current_price = float(data['Close'].iloc[-1])
            current_sma = float(sma.iloc[-1])
            current_upper = float(upper_band.iloc[-1])
            current_lower = float(lower_band.iloc[-1])
            bandwidth = float(current_upper - current_lower)
            
            # Determine position
            if current_price > current_upper:
                position = "ABOVE UPPER BAND"
                signal = "OVERBOUGHT"
                recommendation = "Potential SELL"
            elif current_price < current_lower:
                position = "BELOW LOWER BAND"
                signal = "OVERSOLD"
                recommendation = "Potential BUY"
            else:
                position = "WITHIN BANDS"
                signal = "NEUTRAL"
                recommendation = "Continue monitoring"
            
            volatility = "HIGH" if bandwidth > current_sma * 0.1 else "LOW"
            
            return make_response(jsonify({
                'success': True,
                'symbol': symbol,
                'indicator': 'Bollinger Bands',
                'current_price': round(current_price, 2),
                'upper_band': round(current_upper, 2),
                'middle_band (SMA)': round(current_sma, 2),
                'lower_band': round(current_lower, 2),
                'bandwidth': round(bandwidth, 2),
                'position': position,
                'signal': signal,
                'volatility': volatility,
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat()
            }), 200)
            
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class TechnicalSignalCombined(Resource):
    """GET /api/v1/technical/signal/<symbol> - Combined technical analysis"""
    
    def get(self, symbol):
        """
        Combines RSI, MACD, and Bollinger Bands for holistic signal
        """
        try:
            # Fetch data once
            ticker = symbol if '.' in symbol else f"{symbol}.NS"
            data = yf.download(ticker, period="90d", progress=False)
            
            if data.empty:
                return make_response(jsonify({'error': f'No data for {symbol}'}), 404)
            
            # RSI Calculation
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = float(rsi.iloc[-1])
            
            # MACD Calculation
            ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            current_macd = float(macd_line.iloc[-1])
            current_signal = float(signal_line.iloc[-1])
            
            # Bollinger Bands Calculation
            sma = data['Close'].rolling(window=20).mean()
            std = data['Close'].rolling(window=20).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            current_price = float(data['Close'].iloc[-1])
            current_sma = float(sma.iloc[-1])
            current_upper = float(upper_band.iloc[-1])
            current_lower = float(lower_band.iloc[-1])
            
            # Aggregate signals
            buy_signals = 0
            sell_signals = 0
            
            # RSI signals
            if current_rsi < 30:
                buy_signals += 1
            elif current_rsi > 70:
                sell_signals += 1
            
            # MACD signals
            if current_macd > current_signal:
                buy_signals += 1
            else:
                sell_signals += 1
            
            # Bollinger signals
            if current_price < current_lower:
                buy_signals += 1
            elif current_price > current_upper:
                sell_signals += 1
            
            # Final recommendation
            if buy_signals > sell_signals:
                overall_signal = "BUY"
                confidence = (buy_signals / 3) * 100
            elif sell_signals > buy_signals:
                overall_signal = "SELL"
                confidence = (sell_signals / 3) * 100
            else:
                overall_signal = "HOLD"
                confidence = 50
            
            return make_response(jsonify({
                'success': True,
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'overall_signal': overall_signal,
                'confidence': round(confidence, 1),
                'indicators': {
                    'RSI': {
                        'value': round(current_rsi, 2),
                        'signal': 'OVERSOLD' if current_rsi < 30 else 'OVERBOUGHT' if current_rsi > 70 else 'NEUTRAL'
                    },
                    'MACD': {
                        'value': round(current_macd, 4),
                        'signal': 'BULLISH' if current_macd > current_signal else 'BEARISH'
                    },
                    'Bollinger': {
                        'position': 'BELOW' if current_price < current_lower else 'ABOVE' if current_price > current_upper else 'WITHIN'
                    }
                },
                'signals': {
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals,
                    'out_of': 3
                },
                'recommendation': f"{overall_signal} with {confidence}% confidence. {buy_signals} buy signals, {sell_signals} sell signals detected.",
                'timestamp': datetime.now().isoformat()
            }), 200)
            
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)
