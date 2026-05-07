const { chromium } = require('playwright');

/**
 * 土地数据爬虫 - 使用 Playwright 拦截真实 API 请求
 * 能够处理的城市：北京、上海、广州、深圳等
 */
class LandScraper {
  constructor() {
    this.browser = null;
    this.context = null;
    this.page = null;
    this.apiData = null;
  }

  /**
   * 初始化浏览器
   */
  async init() {
    console.log('🚀 启动浏览器...');
    this.browser = await chromium.launch({
      headless: false, // 设为 false 可以看到浏览器操作过程
      args: ['--disable-blink-features=AutomationControlled']
    });
    
    this.context = await this.browser.newContext({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });
    
    this.page = await this.context.newPage();
    
    // 监听所有请求
    this.page.on('request', request => {
      if (request.url().includes('listForPage') || request.url().includes('land')) {
        console.log('📡 捕获 API 请求:', request.url());
        console.log('📝 请求方法:', request.method());
        console.log('📦 请求体:', request.postData());
      }
    });
    
    // 监听所有响应
    this.page.on('response', async response => {
      if (response.url().includes('listForPage') || response.url().includes('land')) {
        console.log('✅ 捕获 API 响应:', response.url());
        try {
          const text = await response.text();
          console.log('📊 响应内容长度:', text.length);
          
          // 尝试解析 JSON
          if (text.includes('{') || text.includes('[')) {
            try {
              this.apiData = JSON.parse(text);
              console.log('✅ 成功解析 JSON 数据');
            } catch (e) {
              // 可能是加密数据，需要保存
              this.apiData = text;
              console.log('⚠️  数据可能是加密的，已保存原始内容');
            }
          }
        } catch (e) {
          console.log('❌ 读取响应失败:', e.message);
        }
      }
    });
  }

  /**
   * 爬取上海土地数据
   */
  async scrapeShanghai() {
    console.log('\n📍 开始爬取上海土地数据...');
    
    const url = 'https://ghzyj.sh.gov.cn/land_ghsl/';
    
    try {
      // 导航到页面
      console.log('🌐 正在访问:', url);
      await this.page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
      
      // 等待页面完全加载
      console.log('⏳ 等待页面加载完成...');
      await this.page.waitForTimeout(3000);
      
      // 截图看看页面状态
      await this.page.screenshot({ path: 'shanghai_page.png', fullPage: true });
      console.log('📸 已保存页面截图: shanghai_page.png');
      
      // 尝试点击查询按钮或等待数据加载
      console.log('🔍 查找数据列表元素...');
      
      // 等待可能的数据加载
      await this.page.waitForTimeout(5000);
      
      // 尝试获取页面内容
      const pageContent = await this.page.content();
      console.log('📄 页面内容长度:', pageContent.length);
      
      // 检查是否有 list_data 元素
      const listData = await this.page.$('#list_data');
      if (listData) {
        console.log('✅ 找到 #list_data 元素');
        const text = await listData.textContent();
        console.log('📊 数据内容:', text.substring(0, 200));
      } else {
        console.log('⚠️  未找到 #list_data 元素');
      }
      
      return this.apiData;
      
    } catch (error) {
      console.error('❌ 爬取失败:', error.message);
      throw error;
    }
  }

  /**
   * 爬取北京土地数据
   */
  async scrapeBeijing() {
    console.log('\n📍 开始爬取北京土地数据...');
    // TODO: 实现北京的土地数据爬取
    throw new Error('北京土地数据爬取尚未实现');
  }

  /**
   * 爬取广州土地数据
   */
  async scrapeGuangzhou() {
    console.log('\n📍 开始爬取广州土地数据...');
    // TODO: 实现广州的土地数据爬取
    throw new Error('广州土地数据爬取尚未实现');
  }

  /**
   * 爬取深圳土地数据
   */
  async scrapeShenzhen() {
    console.log('\n📍 开始爬取深圳土地数据...');
    // TODO: 实现深圳的土地数据爬取
    throw new Error('深圳土地数据爬取尚未实现');
  }

  /**
   * 关闭浏览器
   */
  async close() {
    if (this.browser) {
      await this.browser.close();
      console.log('\n👋 浏览器已关闭');
    }
  }

  /**
   * 保存数据到文件
   */
  async saveData(data, filename) {
    const fs = require('fs');
    const path = require('path');
    
    const filepath = path.join(__dirname, filename);
    fs.writeFileSync(filepath, JSON.stringify(data, null, 2), 'utf8');
    console.log('💾 数据已保存到:', filepath);
  }
}

// 主函数
async function main() {
  const scraper = new LandScraper();
  
  try {
    // 初始化
    await scraper.init();
    
    // 爬取上海数据
    const shanghaiData = await scraper.scrapeShanghai();
    
    if (shanghaiData) {
      console.log('\n✅ 成功获取上海土地数据!');
      await scraper.saveData(shanghaiData, 'shanghai_land_data.json');
    } else {
      console.log('\n⚠️  未能获取数据，请检查截图和日志');
    }
    
    // 等待用户查看结果
    console.log('\n⏸️  按 Enter 键退出...');
    process.stdin.once('data', () => {
      scraper.close();
      process.exit(0);
    });
    
  } catch (error) {
    console.error('\n❌ 发生错误:', error);
    await scraper.close();
    process.exit(1);
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  main();
}

module.exports = LandScraper;
