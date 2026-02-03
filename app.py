#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import shutil
from bilibili_spider import BilibiliSpider

app = Flask(__name__)

# 检测是否在 Vercel 环境中
is_vercel = os.environ.get('VERCEL', False)

# 设置上传和下载目录
if is_vercel:
    # 在 Vercel 环境中使用临时目录
    app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
    app.config['DOWNLOAD_FOLDER'] = tempfile.gettempdir()
else:
    # 本地环境使用固定目录
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['DOWNLOAD_FOLDER'] = 'downloads'
    # 确保目录存在
    for folder in [app.config['UPLOAD_FOLDER'], app.config['DOWNLOAD_FOLDER']]:
        if not os.path.exists(folder):
            os.makedirs(folder)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def download():
    try:
        # 获取请求参数
        keywords = request.json.get('keywords', '').strip()
        max_downloads = request.json.get('max_downloads', 10)
        
        # 验证参数
        if not keywords:
            return jsonify({'status': 'error', 'message': '关键词不能为空'})
        
        # 在 Vercel 环境中，忽略用户指定的保存路径，使用临时目录
        if is_vercel:
            save_path = app.config['DOWNLOAD_FOLDER']
        else:
            save_path = request.json.get('save_path', app.config['DOWNLOAD_FOLDER'])
            # 确保保存路径存在
            if not os.path.exists(save_path):
                os.makedirs(save_path)
        
        # 创建爬虫实例
        spider = BilibiliSpider()
        spider.download_dir = save_path
        
        # 解析多个关键词
        keywords_list = [k.strip() for k in keywords.replace(',', ' ').split() if k.strip()]
        
        if not keywords_list:
            return jsonify({'status': 'error', 'message': '关键词不能为空'})
        
        # 开始搜索并获取下载链接
        results = []
        total_downloaded = 0
        downloaded_links = set()
        
        for keyword in keywords_list:
            print(f'Processing keyword: {keyword}')
            page = 1
            keyword_downloaded = 0
            
            while keyword_downloaded < max_downloads:
                # 搜索视频
                videos = spider.search_videos(keyword)
                
                if not videos:
                    break
                
                # 处理视频
                for video in videos:
                    if keyword_downloaded >= max_downloads:
                        break
                    
                    if video['link'] in downloaded_links:
                        continue
                    
                    # 记录结果，包含下载链接
                    results.append({
                        'title': video['title'],
                        'link': video['link'],
                        'up': video['up'],
                        'download_link': video.get('download_link', video['link'])
                    })
                    
                    keyword_downloaded += 1
                    total_downloaded += 1
                    downloaded_links.add(video['link'])
            
        return jsonify({
            'status': 'success',
            'message': f'搜索完成，共找到 {total_downloaded} 个视频',
            'results': results,
            'save_path': save_path
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/download/video', methods=['GET'])
def download_video():
    try:
        # 获取视频链接参数
        video_url = request.args.get('url', '').strip()
        
        # 验证参数
        if not video_url:
            return jsonify({'status': 'error', 'message': '视频链接不能为空'})
        
        # 创建爬虫实例
        spider = BilibiliSpider()
        
        # 获取视频内容
        video_content, file_name = spider.get_video_content(video_url)
        
        if not video_content:
            return jsonify({'status': 'error', 'message': '获取视频内容失败'})
        
        # 返回视频文件，设置Content-Disposition头，使浏览器提示下载
        from flask import send_file
        import io
        
        # 创建文件对象
        file_obj = io.BytesIO(video_content)
        
        # 返回文件，设置文件名和MIME类型
        return send_file(
            file_obj,
            as_attachment=True,
            download_name=file_name,
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5678)
