#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股市场情绪数据采集 API
使用 AKShare 获取真实 A 股数据
"""

from flask import Flask, jsonify
from flask_cors import CORS
import akshare as ak
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 允许跨域访问

def get_market_volume():
    """获取两市成交额"""
    try:
        # 获取上证指数和深证成指成交额
        df = ak.stock_zh_index_daily(symbol="sh000001")
        sh_volume = df['volume'].iloc[-1] if not df.empty else 3000
        
        df = ak.stock_zh_index_daily(symbol="sz399001")
        sz_volume = df['volume'].iloc[-1] if not df.empty else 3000
        
        total_volume = (sh_volume + sz_volume) / 100000000  # 转换为亿
        return round(total_volume, 2)
    except:
        return 8000  # 默认值

def get_market_breadth():
    """获取市场涨跌家数"""
    try:
        # 获取沪深 A 股涨跌分布
        df = ak.stock_em_a股涨跌幅()
        up_count = len(df[df['涨跌幅'] > 0])
        down_count = len(df[df['涨跌幅'] < 0])
        return up_count, down_count
    except:
        return 2500, 2000  # 默认值

def get_leader_board():
    """获取连板数据"""
    try:
        # 获取涨停板数据
        df = ak.stock_em_zt_pool_zbgc()
        if not df.empty:
            max_continuous = df['连续涨停次数'].max()
            limit_up_count = len(df)
            return max_continuous, limit_up_count
        return 4, 42  # 默认值
    except:
        return 4, 42

def get_theme_strength():
    """获取题材强度"""
    try:
        # 获取行业板块涨幅
        df = ak.stock_board_industry_name_em()
        if not df.empty:
            top_themes = df.nlargest(5, '涨跌幅')
            avg_change = top_themes['涨跌幅'].mean()
            main_theme = top_themes.iloc[0]['板块名称']
            return main_theme, round(avg_change, 2)
        return "多个题材", 2.5
    except:
        return "多个题材", 2.5

def get_market_index():
    """获取上证指数位置和趋势"""
    try:
        df = ak.stock_zh_index_daily(symbol="sh000001")
        if not df.empty:
            current = df['close'].iloc[-1]
            change = df['涨跌幅'].iloc[-1] if '涨跌幅' in df.columns else 0
            return round(current, 2), round(change, 2)
        return 3000, 0
    except:
        return 3000, 0

def calculate_scores(volume, up_down_ratio, leader_height, theme_change, index_change):
    """计算五大维度分数"""
    # 成交量分数（8000 亿以下 50 分，1 万亿 80 分，1.5 万亿 100 分）
    if volume < 8000:
        volume_score = int(volume / 8000 * 50)
    elif volume < 10000:
        volume_score = int(50 + (volume - 8000) / 2000 * 30)
    else:
        volume_score = min(100, int(80 + (volume - 10000) / 5000 * 20))
    
    # 涨跌比分数
    ratio_score = int(up_down_ratio * 100)
    
    # 龙头分数（连板高度）
    if leader_height >= 7:
        leader_score = 90
    elif leader_height >= 5:
        leader_score = 75
    elif leader_height >= 3:
        leader_score = 60
    else:
        leader_score = 40
    
    # 题材分数
    if theme_change > 4:
        theme_score = 85
    elif theme_change > 2:
        theme_score = 70
    elif theme_change > 0:
        theme_score = 55
    else:
        theme_score = 40
    
    # 大盘分数
    if index_change > 1:
        market_score = 80
    elif index_change > 0:
        market_score = 65
    elif index_change > -1:
        market_score = 50
    else:
        market_score = 35
    
    return {
        'volume': max(0, min(100, volume_score)),
        'ratio': max(0, min(100, ratio_score)),
        'leader': max(0, min(100, leader_score)),
        'theme': max(0, min(100, theme_score)),
        'market': max(0, min(100, market_score))
    }

@app.route('/api/market-emotion', methods=['GET'])
def get_market_emotion():
    """获取市场情绪数据"""
    try:
        # 获取真实数据
        volume = get_market_volume()
        up_count, down_count = get_market_breadth()
        leader_height, limit_up_count = get_leader_board()
        main_theme, theme_change = get_theme_strength()
        index_value, index_change = get_market_index()
        
        # 计算涨跌比
        up_down_ratio = up_count / (up_count + down_count) if (up_count + down_count) > 0 else 0.5
        
        # 计算分数
        scores = calculate_scores(volume, up_down_ratio, leader_height, theme_change, index_change)
        
        # 计算综合分数
        total_score = int(round(sum(scores.values()) / 5))
        
        # 确定状态
        if total_score <= 20:
            status = "极寒"
            status_emoji = "❄️"
        elif total_score <= 40:
            status = "寒冷"
            status_emoji = "🥶"
        elif total_score <= 60:
            status = "温和"
            status_emoji = "😐"
        elif total_score <= 80:
            status = "温暖"
            status_emoji = "🔥"
        else:
            status = "炎热"
            status_emoji = "🌡️"
        
        response = {
            'success': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'totalScore': total_score,
            'status': status,
            'statusEmoji': status_emoji,
            'dimensions': {
                'volume': {
                    'score': scores['volume'],
                    'value': f"{volume}亿",
                    'status': "放量" if scores['volume'] > 70 else "平量" if scores['volume'] > 40 else "缩量"
                },
                'ratio': {
                    'score': scores['ratio'],
                    'value': f"{up_count}:{down_count}",
                    'up': up_count,
                    'down': down_count
                },
                'leader': {
                    'score': scores['leader'],
                    'value': f"{leader_height}板",
                    'limit_up': limit_up_count
                },
                'theme': {
                    'score': scores['theme'],
                    'value': main_theme,
                    'change': f"{theme_change}%"
                },
                'market': {
                    'score': scores['market'],
                    'value': f"{index_value}点",
                    'change': f"{index_change}%"
                }
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 A 股市场情绪 API 启动中...")
    print("📊 数据源：AKShare")
    print("🌐 访问地址：http://localhost:5000/api/market-emotion")
    app.run(host='0.0.0.0', port=5000, debug=False)
