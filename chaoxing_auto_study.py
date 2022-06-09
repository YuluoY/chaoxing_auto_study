from selenium import webdriver
import time
import pickle
import requests
import re
from datetime import datetime
import os
import sys
import math


def close(wd):
    global nonVideoCount, totalTime, totalTitle, programRunningTime
    print(f'\n=============🎉🎉🎉🎉🎉=============='
          f'\n自动跳过非视频任务点：{nonVideoCount}个'
          f'\n自动播放任务点视频：{len(list(totalTitle.keys()))}个'
          f'\n自动播放视频时长：{formatTime(second=totalTime, format="%H时%M分%S秒")}'
          f'\n程序共运行时长：{formatTime(second=programRunningTime, format="%H时%M分%S秒")}'
          f'\n为您播放的所有章节及时长：{totalTitle}'
          f'\n感想您的使用，所有视频都已播放完毕！'
          f'\n=============🎉🎉🎉🎉🎉==============')
    wd.close()  # 关闭驱动
    sys.exit(0)  # 结束程序
    os.system('taskkill /im chromedriver.exe /F')  # 杀死谷歌驱动进程


# 获取登录的cookies数据
def getCookies():
    try:
        t = 0;
        wd = webdriver.Chrome(CHROME_DRIVER_PATH)  # 创建浏览器驱动对象
        wd.implicitly_wait(60)  # 隐式等待
        wd.get(TARGET_PATH)  # 打开目标地址
        currTitle = wd.title;
        while True:
            time.sleep(1)
            t += 1
            if wd.title != currTitle: break
            if t >= MAX_WAIT_TIME:
                print("因用户长时间未操作，程序已自动关闭！")
                wd.quit()
            print(f"\r用户正进行登录操作中，已等待{t}秒", end="")
        time.sleep(3)
        cookies = wd.get_cookies()  # 获取cookies数据
        return cookies
    except Exception as e:
        print(e)
    finally:
        wd.close()
        os.system('taskkill /im chromedriver.exe /F')  # 杀死谷歌驱动进程


# 存储登录的cookies数据
def memoryCookies(cookies):
    with open(COOKIES_PATH, 'wb') as f:
        pickle.dump(cookies, f)


def getLocalCookiesData():
    with open(COOKIES_PATH, 'rb') as fp:  # 打开文件，取出cookies信息
        data = pickle.load(fp)
        print(data)
        return data


# cookies注入
def cookieInjection(wd):
    try:
        with open(COOKIES_PATH, "rb") as f:
            # 从文件获取cookies，并转化成list对象
            cookies = pickle.load(f)
        # 遍历每一条cookies，把登录的cookies传入到企业微信中
        for cookie in cookies:
            # 由于selenium的cookies不支持expiry，所以需要去掉
            # if "expiry" in cookie.keys():
            #     # dict支持pop的删除函数
            #     cookie.pop("expiry")
            # # 添加cookies
            wd.add_cookie(cookie)
        return wd
    except:
        return wd


# 分钟转换秒  例如：1:33  返回：93
def minuteToSecond(str):
    list = str.split(":")
    return int(list[0]) * 60 + int(list[1])


# 视频播放
def videoPlay(title):
    global nonVideoCount, totalTime, totalTitle, programRunningTime
    try:  # 尝试深入内部框架，出现错误就略过，说明没有iframe标签
        wd.switch_to.frame(wd.find_element_by_id('iframe'))
        wd.switch_to.frame(wd.find_element_by_tag_name("iframe"))
    except:
        pass

    try:  # 尝试获取播放按钮 出现错误说明该任务点无可播放的视频，就切换下一任务点
        playBtn = wd.find_element_by_tag_name(".vjs-big-play-button")  # 播放按钮
        playBtn.click()
        muteBtn = wd.find_element_by_css_selector('[class="vjs-mute-control vjs-control vjs-button vjs-vol-3"]')  # 静音
        wd.execute_script("$(arguments[0]).click()", muteBtn)
        time.sleep(2)
    except Exception as e:
        nonVideoCount += 1  # 播放按钮获取失败 非视频+1
        nextChapterChange()

    # 播放速度按钮
    playSpeed = wd.find_element_by_css_selector(
        '[class="vjs-playback-rate vjs-menu-button vjs-menu-button-popup vjs-button"]')

    # 将播放速度调到最高倍速 2倍速
    playSpeed.click()
    playSpeed.click()
    playSpeed.click()

    currPlayTime = wd.find_element_by_css_selector(".vjs-current-time-display").text  # 当前播放进度时间
    endPlayTime = wd.find_element_by_css_selector('.vjs-duration-display').text  # 结束时间
    duration = minuteToSecond(endPlayTime) - minuteToSecond(currPlayTime)  # 持续时间 单位：s
    totalTime += duration / 2  # 统计全部时间
    totalTitle[title] = f"{formatTime(duration, '%H时%M分%S秒')}"  # 统计标题和时间

    while True:
        # 获取播放进度条
        progress = wd.find_element_by_css_selector('[class="vjs-play-progress vjs-slider-bar"]').get_attribute("style")
        time.sleep(1)
        programRunningTime += 1  # 记录程序运行秒数

        if minuteToSecond(endPlayTime) == 0.0:
            endPlayTime = wd.find_element_by_css_selector('.vjs-duration-display').text  # 结束时间

        print(
            f'\r当前任务点：{title}，{progress.replace("width", "播放进度")}，预计播放时间：{formatTime(minuteToSecond(endPlayTime), "%H时%M分%S秒")}',
            end="")
        if (progress.split(" ")[1] == "100%;"):  # 当播放进度达到100 就切换下一任务点
            print()
            nextChapterChange()


def formatTime(second, format):
    return time.strftime(format, time.gmtime(second))


# 切换章节
def nextChapterChange():
    global totalTitle
    totalTitle.keys()
    wd.switch_to.default_content()
    next = wd.find_element_by_css_selector('[class="jb_btn jb_btn_92 fs14 prev_next next"]')
    wd.execute_script("$(arguments[0]).click()", next)  # 章节切换
    time.sleep(2)  # 休眠2秒，等页面完全打开再进行下一步操作
    title = wd.find_element_by_css_selector(".prev_title").text
    if title in list(totalTitle.keys()):  # 如果任务标题存在重复说明视频已全部播放完毕
        close(wd=wd)
    else:
        videoPlay(title)


if __name__ == '__main__':
    COOKIES_PATH = './cookies.txt'  # cookies的存放路径
    CHROME_DRIVER_PATH = "D:\\桌面\\chromedriver.exe"  # 谷歌驱动器的路径
    LOGIN_PATH = 'https://hbuas.mh.chaoxing.com/'
    # 目标地址，即视频播放地址
    TARGET_PATH = 'https://mooc1.chaoxing.com/mycourse/studentstudy?chapterId=137277437&courseId=202717818&clazzid=47883546&cpi=96175171&enc=bdeeb9eccac761f9d9141c626514f06a&mooc2=1&openc=ef88119ed10bb184e8431d120989363a'
    MAX_WAIT_TIME = 300  # 最大等待时间 5分钟

    nonVideoCount = 0  # 统计非视频任务点数量
    totalTime = 0  # 统计播放视频总共时间
    programRunningTime = 0  # 程序运行时间
    totalTitle = {}  # 统计任务点标题
    sys.setrecursionlimit(9999999)

    if os.path.exists(COOKIES_PATH) == False:  # 如果当前文件目录下没有cookies.bat文件，就进行登录操作获取饼干
        memoryCookies(getCookies())  # 存储cookies

    wd = webdriver.Chrome(CHROME_DRIVER_PATH)
    wd.implicitly_wait(60)
    wd.get(LOGIN_PATH)  # 进入登录界面
    wd = cookieInjection(wd)  # 饼干注入
    wd.get(TARGET_PATH)  # 打开目标界面
    chapterTitle = wd.find_element_by_css_selector(".prev_title").text  # 获取当前任务点的标题
    videoPlay(chapterTitle)

