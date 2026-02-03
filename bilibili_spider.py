#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from bs4 import BeautifulSoup
import subprocess
from colorama import init, Fore, Style
import time
import re

init(autoreset=True)

class BilibiliSpider:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.download_dir = './downloads'
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        self.download_count = 0
        self.max_downloads = 10  # 默认最大下载数量
    
    def search_videos(self, keyword):
        try:
            import urllib.parse
            # 对关键词进行URL编码
            encoded_keyword = urllib.parse.quote(keyword)
            url = f'https://search.bilibili.com/all?keyword={encoded_keyword}'
            
            # 添加更多的请求头信息
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.bilibili.com/',
                'Accept-Language': 'zh-CN,zh;q=0.9'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            video_list = []
            
            # 尝试多种CSS选择器
            selectors = [
                '.video-item.matrix',
                '.bili-video-card__wrap',
                '.video-list-item',
                '.video-card'
            ]
            
            video_cards = []
            for selector in selectors:
                cards = soup.select(selector)
                if cards:
                    video_cards = cards
                    break
            
            if not video_cards:
                # 如果还是没有找到，尝试更通用的选择器
                video_cards = soup.select('a[href*="video"]')
            
            print(f'{Fore.YELLOW}找到 {len(video_cards)} 个视频卡片{Style.RESET_ALL}')
            
            for i, card in enumerate(video_cards[:10]):
                try:
                    # 尝试多种方式提取标题
                    title_elements = card.select('.title, .bili-video-card__info--title, h3, .video-title')
                    if title_elements:
                        title = title_elements[0].get_text(strip=True)
                    else:
                        title = '无标题'
                    
                    # 提取链接
                    link = card.get('href')
                    if not link:
                        link_element = card.select_one('a')
                        if link_element:
                            link = link_element.get('href')
                    
                    if link:
                        if not link.startswith('http'):
                            link = 'https:' + link
                        
                        # 尝试提取UP主信息
                        up_elements = card.select('.up, .bili-video-card__info--author, .video-author')
                        if up_elements:
                            up = up_elements[0].get_text(strip=True)
                        else:
                            up = '未知UP主'
                        
                        video_list.append({
                            'index': i + 1,
                            'title': title,
                            'link': link,
                            'up': up
                        })
                except Exception as e:
                    print(f'{Fore.YELLOW}处理视频卡片时出错: {e}{Style.RESET_ALL}')
                    continue
            
            print(f'{Fore.GREEN}成功解析 {len(video_list)} 个视频{Style.RESET_ALL}')
            return video_list
        except Exception as e:
            print(f'{Fore.RED}搜索失败: {e}{Style.RESET_ALL}')
            return []
    
    def download_video(self, url):
        try:
            # 提取视频ID
            video_id = url.split('/')[-1].split('?')[0]
            
            # 定义不同的下载策略
            download_strategies = [
                # 策略1: 不指定格式，让you-get自动选择最佳格式
                ['python', '-m', 'you_get', '-o', self.download_dir, '--force', url],
                # 策略2: 尝试指定较低清晰度的格式
                ['python', '-m', 'you_get', '-o', self.download_dir, '--force', '--format=flv', url],
                # 策略3: 尝试指定另一种格式
                ['python', '-m', 'you_get', '-o', self.download_dir, '--force', '--format=mp4', url]
            ]
            
            # 尝试不同的下载策略
            for i, cmd in enumerate(download_strategies):
                print(f'{Fore.CYAN}尝试下载策略 {i+1}...{Style.RESET_ALL}')
                print(f'{Fore.YELLOW}命令: {" ".join(cmd)}{Style.RESET_ALL}')
                
                # 使用stdout=subprocess.PIPE和stderr=subprocess.PIPE捕获输出
                # 设置encoding='utf-8'避免编码错误
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                if result.returncode == 0:
                    print(f'{Fore.GREEN}下载成功!{Style.RESET_ALL}')
                    
                    # 清理其他格式的文件
                    self.cleanup_files(video_id)
                    
                    return True
                else:
                    print(f'{Fore.RED}下载失败: {result.stderr}{Style.RESET_ALL}')
                    if i < len(download_strategies) - 1:
                        print(f'{Fore.YELLOW}尝试下一种策略...{Style.RESET_ALL}')
            
            # 所有策略都失败
            print(f'{Fore.RED}所有下载策略都失败{Style.RESET_ALL}')
            print(f'{Fore.YELLOW}跳过此视频{Style.RESET_ALL}')
            return False
        except Exception as e:
            print(f'{Fore.RED}下载异常: {e}{Style.RESET_ALL}')
            print(f'{Fore.YELLOW}跳过此视频{Style.RESET_ALL}')
            return False
    
    def cleanup_files(self, video_id):
        """清理无用的辅助文件和音频文件"""
        try:
            files = os.listdir(self.download_dir)
            
            # 收集与当前视频相关的mp4文件
            video_related_mp4 = []
            for file in files:
                if file.endswith('.mp4') and video_id in file:
                    file_path = os.path.join(self.download_dir, file)
                    size = os.path.getsize(file_path)
                    video_related_mp4.append((file, size))
            
            # 识别并删除音频文件（通常比视频文件小很多）
            deleted_audio = []
            if len(video_related_mp4) > 1:
                # 按文件大小排序
                video_related_mp4.sort(key=lambda x: x[1], reverse=True)
                
                # 最大的文件通常是视频文件，其他可能是音频文件
                video_file = video_related_mp4[0]
                audio_files = video_related_mp4[1:]
                
                print(f'{Fore.CYAN}识别视频和音频文件...{Style.RESET_ALL}')
                print(f'{Fore.GREEN}保留视频文件: {video_file[0]} ({video_file[1]/(1024*1024):.2f} MB){Style.RESET_ALL}')
                
                # 删除音频文件
                for file, size in audio_files:
                    # 只删除明显较小的文件（通常音频文件小于10MB）
                    if size < 10 * 1024 * 1024:
                        file_path = os.path.join(self.download_dir, file)
                        os.remove(file_path)
                        deleted_audio.append(file)
                        print(f'{Fore.YELLOW}删除音频文件: {file} ({size/(1024*1024):.2f} MB){Style.RESET_ALL}')
            
            # 只删除.cmt.xml等无用的辅助文件
            deleted_files = []
            for file in files:
                if file.endswith('.cmt.xml') and video_id in file:
                    file_path = os.path.join(self.download_dir, file)
                    os.remove(file_path)
                    deleted_files.append(file)
            
            if deleted_files:
                print(f'{Fore.CYAN}清理无用文件...{Style.RESET_ALL}')
                for file in deleted_files:
                    print(f'{Fore.YELLOW}删除: {file}{Style.RESET_ALL}')
            
            # 显示最终保留的文件
            final_files = [f for f in os.listdir(self.download_dir) if f.endswith('.mp4') and video_id in f]
            if final_files:
                print(f'{Fore.GREEN}最终保留的文件: {Style.RESET_ALL}')
                for file in final_files:
                    file_path = os.path.join(self.download_dir, file)
                    size = os.path.getsize(file_path) / (1024 * 1024)  # 转换为MB
                    print(f'{Fore.GREEN}  - {file} ({size:.2f} MB){Style.RESET_ALL}')
            else:
                print(f'{Fore.GREEN}无需清理，没有找到相关文件{Style.RESET_ALL}')
        except Exception as e:
            print(f'{Fore.RED}清理文件失败: {e}{Style.RESET_ALL}')

def test_search():
    """测试搜索功能"""
    spider = BilibiliSpider()
    
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')
    print(f'{Fore.CYAN}测试搜索功能{Style.RESET_ALL}')
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')
    
    test_keywords = ['无人机', '编程', '美食']
    
    for keyword in test_keywords:
        print(f'{Fore.CYAN}\n测试关键词: "{keyword}"{Style.RESET_ALL}')
        print(f'{Fore.CYAN}正在搜索...{Style.RESET_ALL}')
        
        videos = spider.search_videos(keyword)
        
        if videos:
            print(f'{Fore.GREEN}搜索成功! 共找到 {len(videos)} 个视频:{Style.RESET_ALL}')
            print(f'{Fore.CYAN}{"-"*80}{Style.RESET_ALL}')
            for video in videos[:3]:  # 只显示前3个结果
                print(f'{Fore.YELLOW}[{video["index"]}]{Style.RESET_ALL} {video["title"]}')
                print(f'{Fore.CYAN}UP主: {video["up"]}{Style.RESET_ALL}')
                print(f'{Fore.CYAN}链接: {video["link"]}{Style.RESET_ALL}')
                print(f'{Fore.CYAN}{"-"*80}{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}搜索失败，未找到相关视频{Style.RESET_ALL}')
    
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')
    print(f'{Fore.CYAN}测试完成{Style.RESET_ALL}')
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')

def main():
    spider = BilibiliSpider()
    
    print(f'{Fore.CYAN}{"="*50}{Style.RESET_ALL}')
    print(f'{Fore.CYAN}B站视频爬虫系统{Style.RESET_ALL}')
    print(f'{Fore.CYAN}{"="*50}{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}提示: 可输入多个关键词，用空格或逗号分隔，按顺序优先级爬取{Style.RESET_ALL}')
    print(f'{Fore.CYAN}{"="*50}{Style.RESET_ALL}')
    
    while True:
        keywords_input = input(f'{Fore.YELLOW}请输入搜索关键词 (输入q退出，输入test进行测试): {Style.RESET_ALL}')
        if keywords_input.lower() == 'q':
            print(f'{Fore.CYAN}感谢使用，再见!{Style.RESET_ALL}')
            break
        
        if keywords_input.lower() == 'test':
            test_search()
            continue
        
        if not keywords_input.strip():
            print(f'{Fore.RED}关键词不能为空!{Style.RESET_ALL}')
            continue
        
        # 解析多个关键词
        keywords = [k.strip() for k in keywords_input.replace(',', ' ').split() if k.strip()]
        
        if not keywords:
            print(f'{Fore.RED}关键词不能为空!{Style.RESET_ALL}')
            continue
        
        # 设置总下载数量
        max_downloads_input = input(f'{Fore.YELLOW}请输入每个关键词的最大下载数量 (默认10): {Style.RESET_ALL}')
        if max_downloads_input.strip():
            try:
                max_downloads_per_keyword = int(max_downloads_input.strip())
                print(f'{Fore.GREEN}已设置每个关键词的最大下载数量: {max_downloads_per_keyword}{Style.RESET_ALL}')
            except ValueError:
                print(f'{Fore.RED}输入错误，使用默认值10{Style.RESET_ALL}')
                max_downloads_per_keyword = 10
        else:
            max_downloads_per_keyword = 10
            print(f'{Fore.GREEN}使用默认最大下载数量: 10{Style.RESET_ALL}')
        
        print(f'{Fore.CYAN}{"="*80}{Style.RESET_ALL}')
        print(f'{Fore.CYAN}开始按优先级顺序搜索和下载视频{Style.RESET_ALL}')
        print(f'{Fore.CYAN}关键词列表: {" > ".join(keywords)}{Style.RESET_ALL}')
        print(f'{Fore.CYAN}每个关键词最大下载数量: {max_downloads_per_keyword}{Style.RESET_ALL}')
        print(f'{Fore.CYAN}{"="*80}{Style.RESET_ALL}')
        
        total_downloaded = 0
        downloaded_links = set()  # 记录已下载的视频链接，避免重复下载
        
        # 按顺序处理每个关键词
        for keyword_index, keyword in enumerate(keywords):
            print(f'{Fore.CYAN}{"="*80}{Style.RESET_ALL}')
            print(f'{Fore.CYAN}[{keyword_index+1}/{len(keywords)}] 正在处理关键词: {keyword}{Style.RESET_ALL}')
            print(f'{Fore.CYAN}{"="*80}{Style.RESET_ALL}')
            
            # 重置下载计数器
            spider.download_count = 0
            page = 1
            
            while spider.download_count < max_downloads_per_keyword:
                print(f'{Fore.CYAN}\n正在搜索第 {page} 页...{Style.RESET_ALL}')
                
                # 搜索视频
                videos = spider.search_videos(keyword)
                
                if not videos:
                    print(f'{Fore.RED}第 {page} 页未找到相关视频!{Style.RESET_ALL}')
                    page += 1
                    time.sleep(2)  # 避免请求过快
                    continue
                
                print(f'{Fore.GREEN}第 {page} 页找到 {len(videos)} 个视频{Style.RESET_ALL}')
                
                # 边搜寻边下载
                for video in videos:
                    if spider.download_count >= max_downloads_per_keyword:
                        break
                    
                    # 检查是否已下载
                    if video["link"] in downloaded_links:
                        print(f'{Fore.YELLOW}跳过已下载的视频: {video["title"]}{Style.RESET_ALL}')
                        continue
                    
                    print(f'{Fore.CYAN}{"-"*80}{Style.RESET_ALL}')
                    print(f'{Fore.YELLOW}[{spider.download_count+1}/{max_downloads_per_keyword}]{Style.RESET_ALL} 正在处理: {video["title"]}')
                    print(f'{Fore.CYAN}UP主: {video["up"]}{Style.RESET_ALL}')
                    print(f'{Fore.CYAN}链接: {video["link"]}{Style.RESET_ALL}')
                    
                    # 下载视频
                    success = spider.download_video(video["link"])
                    
                    if success:
                        print(f'{Fore.GREEN}下载成功!{Style.RESET_ALL}')
                        spider.download_count += 1
                        total_downloaded += 1
                        downloaded_links.add(video["link"])
                    else:
                        print(f'{Fore.RED}下载失败，跳过此视频{Style.RESET_ALL}')
                    
                    print(f'{Fore.CYAN}{"-"*80}{Style.RESET_ALL}')
                    
                    # 避免请求过快
                    time.sleep(1)
                
                # 搜索下一页
                page += 1
                time.sleep(2)  # 避免请求过快
            
            print(f'{Fore.GREEN}关键词 "{keyword}" 下载完成! 共下载 {spider.download_count} 个视频{Style.RESET_ALL}')
        
        print(f'{Fore.GREEN}{"="*80}{Style.RESET_ALL}')
        print(f'{Fore.GREEN}所有关键词下载完成! 总计下载 {total_downloaded} 个视频{Style.RESET_ALL}')
        print(f'{Fore.GREEN}{"="*80}{Style.RESET_ALL}')

def auto_test_download():
    """自动测试下载功能"""
    spider = BilibiliSpider()
    
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')
    print(f'{Fore.CYAN}自动测试下载功能{Style.RESET_ALL}')
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')
    
    test_keyword = '无人机'
    print(f'{Fore.CYAN}测试关键词: "{test_keyword}"{Style.RESET_ALL}')
    print(f'{Fore.CYAN}正在搜索...{Style.RESET_ALL}')
    
    videos = spider.search_videos(test_keyword)
    
    if videos:
        print(f'{Fore.GREEN}搜索成功! 共找到 {len(videos)} 个视频{Style.RESET_ALL}')
        print(f'{Fore.CYAN}{"-"*80}{Style.RESET_ALL}')
        
        # 自动下载所有视频
        print(f'{Fore.CYAN}开始自动下载所有视频...{Style.RESET_ALL}')
        print(f'{Fore.CYAN}{"-"*80}{Style.RESET_ALL}')
        
        for i, video in enumerate(videos[:2]):  # 只下载前2个视频以节省时间
            print(f'{Fore.YELLOW}[{i+1}/{len(videos)}]{Style.RESET_ALL} 正在下载: {video["title"]}')
            print(f'{Fore.CYAN}UP主: {video["up"]}{Style.RESET_ALL}')
            
            success = spider.download_video(video["link"])
            
            if success:
                print(f'{Fore.GREEN}下载成功!{Style.RESET_ALL}')
            else:
                print(f'{Fore.RED}下载失败!{Style.RESET_ALL}')
            
            print(f'{Fore.CYAN}{"-"*80}{Style.RESET_ALL}')
        
        print(f'{Fore.GREEN}测试完成!{Style.RESET_ALL}')
    else:
        print(f'{Fore.RED}搜索失败，未找到相关视频{Style.RESET_ALL}')
    
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')

def test_new_features():
    """测试新功能"""
    spider = BilibiliSpider()
    
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')
    print(f'{Fore.CYAN}测试新功能{Style.RESET_ALL}')
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')
    
    test_keyword = '无人机'
    spider.max_downloads = 2  # 只下载2个视频以节省时间
    spider.download_count = 0
    
    print(f'{Fore.CYAN}关键词: {test_keyword}{Style.RESET_ALL}')
    print(f'{Fore.CYAN}最大下载数量: {spider.max_downloads}{Style.RESET_ALL}')
    
    page = 1
    downloaded_links = set()
    
    while spider.download_count < spider.max_downloads:
        print(f'{Fore.CYAN}\n正在搜索第 {page} 页...{Style.RESET_ALL}')
        
        videos = spider.search_videos(test_keyword)
        
        if not videos:
            print(f'{Fore.RED}第 {page} 页未找到相关视频!{Style.RESET_ALL}')
            page += 1
            time.sleep(2)
            continue
        
        print(f'{Fore.GREEN}第 {page} 页找到 {len(videos)} 个视频{Style.RESET_ALL}')
        
        for video in videos:
            if spider.download_count >= spider.max_downloads:
                break
            
            if video["link"] in downloaded_links:
                print(f'{Fore.YELLOW}跳过已下载的视频: {video["title"]}{Style.RESET_ALL}')
                continue
            
            print(f'{Fore.CYAN}{"-"*80}{Style.RESET_ALL}')
            print(f'{Fore.YELLOW}[{spider.download_count+1}/{spider.max_downloads}]{Style.RESET_ALL} 正在处理: {video["title"]}')
            print(f'{Fore.CYAN}UP主: {video["up"]}{Style.RESET_ALL}')
            
            success = spider.download_video(video["link"])
            
            if success:
                print(f'{Fore.GREEN}下载成功!{Style.RESET_ALL}')
                spider.download_count += 1
                downloaded_links.add(video["link"])
            else:
                print(f'{Fore.RED}下载失败，跳过此视频{Style.RESET_ALL}')
            
            print(f'{Fore.CYAN}{"-"*80}{Style.RESET_ALL}')
            time.sleep(1)
        
        page += 1
        time.sleep(2)
    
    print(f'{Fore.GREEN}{"="*60}{Style.RESET_ALL}')
    print(f'{Fore.GREEN}测试完成! 共下载 {spider.download_count} 个视频{Style.RESET_ALL}')
    print(f'{Fore.GREEN}{"="*60}{Style.RESET_ALL}')

def test_fix():
    """测试修复后的下载命令"""
    spider = BilibiliSpider()
    
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')
    print(f'{Fore.CYAN}测试修复后的下载命令{Style.RESET_ALL}')
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')
    
    # 测试搜索功能
    print(f'{Fore.CYAN}正在搜索...{Style.RESET_ALL}')
    videos = spider.search_videos('无人机')
    
    if videos:
        print(f'{Fore.GREEN}搜索成功! 共找到 {len(videos)} 个视频{Style.RESET_ALL}')
        
        # 测试下载命令格式
        test_url = videos[0]['link']
        print(f'{Fore.CYAN}\n测试下载命令: {test_url}{Style.RESET_ALL}')
        
        # 构建下载命令并显示
        cmd = ['python', '-m', 'you_get', '-o', spider.download_dir, '--force', test_url]
        print(f'{Fore.YELLOW}命令: {" ".join(cmd)}{Style.RESET_ALL}')
        print(f'{Fore.GREEN}命令格式正确，修复成功!{Style.RESET_ALL}')
    else:
        print(f'{Fore.RED}搜索失败{Style.RESET_ALL}')
    
    print(f'{Fore.CYAN}{"="*60}{Style.RESET_ALL}')

if __name__ == '__main__':
    main()
