import shutil
import gzip
from io import BytesIO
import os, traceback, re
from urllib.error import URLError
from urllib import request, parse
from bs4 import BeautifulSoup


class Image(object):
    ImageMainPath = "./images/main"  # 主图存放路径
    ImageDetailPath = "./images/detail"  # 详情图存放路径
    imgMainList = []  # 主图列表
    imgDetailList = []  # 详情图列表
    UserAgent = "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)"

    def __init__(self, url, urlType):
        self.url = url
        self.urlType = urlType
        # 获取执行方法
        self.handleFunc = {"1688": self.getAli, "taobao": self.getTaobao}.get(urlType)
        self.__initPath()

    def __setHeader(self, req):
        req.add_header("User-Agent", self.UserAgent)

    def __initPath(self):
        try:
            # 删除目录
            shutil.rmtree(self.ImageMainPath)
            shutil.rmtree(self.ImageDetailPath)
        except:
            pass
        # 创建目录
        os.makedirs(self.ImageMainPath)
        os.makedirs(self.ImageDetailPath)


    def __mRequest(self, url):
        req = request.Request(url)
        self.__setHeader(req)
        return request.urlopen(req)

    def parse(self):
        with self.__mRequest(self.url) as f:
            soup = BeautifulSoup(f, 'html.parser')
            self.handleFunc(soup)

    def downloadImg(self, imgList, path):
        imgLen = len(imgList)
        if imgLen == 0:
            print("没有获取到图片")
            return

        for i in range(len(imgList)):
            curImgUrl = imgList[i]
            with self.__mRequest(curImgUrl) as req:
                imgSplit = os.path.split(curImgUrl)
                with open(path + "/" + imgSplit[-1], "wb") as f:
                    f.write(req.read())
        print("下载完成, 请查看" + path + "文件夹")

    def getTaobao(self, s):
        urlTuple = parse.urlparse(self.url)
        proto = urlTuple.scheme
        taobaoCDNPrefixUrl = "http://img.alicdn.com/bao/uploaded/"
        itemPattern = re.compile(r"tds.alicdn.com/json/item_imgs.htm[^\s]*", re.MULTILINE | re.DOTALL)
        scriptSoup = s.find("script", text=itemPattern)
        detailUrl = itemPattern.search(scriptSoup.text).group().replace("',", "")
        detailUrl = proto + "://" + detailUrl
        with self.__mRequest(detailUrl) as f:
            imgApiContent = f.read()
            # 处理gzip
            buff = BytesIO(imgApiContent)  # 把content转为文件对象
            f = gzip.GzipFile(fileobj=buff)
            imgApiContent = f.read().decode('utf-8')
            imgPattern = re.compile(r"([^\"]*.(jpg|png))")
            imgTuple = imgPattern.findall(imgApiContent)
            for i in imgTuple:
                imgPath = i[0]
                self.imgMainList.append(taobaoCDNPrefixUrl + imgPath)

    def getAli(self, soup):
        # 详情图
        detailObj = soup.find(id="desc-lazyload-container")
        imageUrl = detailObj.attrs["data-tfs-url"]
        imageData = self.__mRequest(imageUrl).read()
        imageSoup = BeautifulSoup(imageData, 'html.parser')
        imgDetailList = imageSoup.find_all("img")
        for i in imgDetailList:
            self.imgDetailList.append( i.attrs["src"].replace('\\"', "") )

        # 主图
        mainImgList = soup.select("#dt-tab .tab-trigger .vertical-img>.box-img>img")
        for i in mainImgList:
            try:
                rep = i.attrs['data-lazy-src'].replace('\\"', "").replace('60x60','600x600').replace('_.webp','')
            except Exception:
                rep = i.attrs["src"].replace('\\"', "").replace('60x60','600x600').replace('_.webp','')
            self.imgMainList.append(rep)


if __name__ == "__main__":
    while 1:
        # downloadPath = input("请输入下载地址:")
        # if downloadPath == "":
        #     print("没有下载地址")
        #     continue
        url = input("请粘贴链接:")
        if url == "":
            print("没有输入链接")
            continue

        urlType = "1688"
        print("已输入链接, 开始解析..:", url)
        if "taobao.com" in url:
            urlType = "taobao"
        try:
            img = Image(url, urlType)
            img.parse()
            img.downloadImg(img.imgMainList, img.ImageMainPath)
            img.downloadImg(img.imgDetailList, img.ImageDetailPath)
            print("\n\n")
        except ValueError as e:
            print("值错误: ", e)
        except URLError as e:
            print("请求链接错误: ", e)
        except Exception as e:
            traceback.print_exc()

        continue
