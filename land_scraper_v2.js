const { chromium } = require('playwright');

/**
 * 统一土地数据爬虫
 * 支持城市：上海、北京、广州、深圳等
 * 使用 Playwright 拦截真实 API 请求
 */

class LandDataScraper {
  constructor(options = {}) {
    this.browser = null;
    this.context = null;
    this.page = null;
    this.interceptedData = [];
    
    // 配置选项
    this.options = {
      headless: options.headless || false,
      timeout: options.timeout || 60000,
      screenshotPath: options.screenshotPath || './screenshots',
      ...options
    };
  }

  /**
   * 初始化浏览器
   */
  async init() {
    console.log('🚀 初始化浏览器...');
    
    this.browser = await chromium.launch({
      headless: this.options.headless,
      slowMo: 100,
      args: [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox'
      ]
    });
    
    this.context = await this.browser.newContext({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      viewport: { width: 1920, height: 1080 },
      locale: 'zh-CN'
    });
    
    this.page = await this.context.newPage();
    
    // 设置请求拦截
    this.setupInterceptors();
    
    console.log('✅ 浏览器初始化完成');
  }

  /**
   * 设置请求和响应拦截器
   */
  setupInterceptors() {
    // 拦截请求
    this.page.on('request', (request) => {
      const url = request.url();
      if (this.isTargetAPI(url)) {
        console.log('\n📡 [请求]', this.simplifyURL(url));
        console.log('   方法:', request.method());
        
        const postData = request.postData();
        if (postData) {
          console.log('   请求体:', postData.substring(0, 300));
        }
        
        this.interceptedData.push({
          type: 'request',
          url: url,
          method: request.method(),
          headers: request.headers(),
          postData: postData,
          timestamp: new Date().toISOString()
        });
      }
    });
    
    // 拦截响应
    this.page.on('response', async (response) => {
      const url = response.url();
      if (this.isTargetAPI(url)) {
        console.log('\n✅ [响应]', this.simplifyURL(url));
        console.log('   状态码:', response.status());
        
        try {
          const text = await response.text();
          console.log('   响应长度:', text.length);
          console.log('   响应预览:', text.substring(0, 200));
          
          this.interceptedData.push({
            type: 'response',
            url: url,
            status: response.status(),
            headers: response.headers(),
            body: text,
            timestamp: new Date().toISOString()
          });
        } catch (e) {
          console.log('   ⚠️  读取响应失败:', e.message);
        }
      }
    });
  }

  /**
   * 判断是否为目标 API
   */
  isTargetAPI(url) {
    const targetKeywords = [
      'listForPage',
      'land',
      'ghsl',
      'api',
      'query',
      'search'
    ];
    
    return targetKeywords.some(keyword => url.includes(keyword));
  }

  /**
   * 简化 URL 显示
   */
  simplifyURL(url) {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname + urlObj.pathname;
    } catch {
      return url;
    }
  }

  /**
   * 爬取上海土地数据
   */
  async scrapeShanghai() {
    console.log('\n📍 开始爬取：上海土地供应数据');
    console.log('=' .repeat(60));
    
    const url = 'https://ghzyj.sh.gov.cn/land_ghsl/';
    
    try {
      // 访问页面
      console.log('🌐 访问页面:', url);
      await this.page.goto(url, { 
        waitUntil: 'networkidle',
        timeout: this.options.timeout
      });
      
      console.log('✅ 页面加载完成');
      
      // 等待页面渲染
      await this.page.waitForTimeout(3000);
      
      // 截图
      const screenshotPath = `${this.options.screenshotPath}/shanghai_land_page.png`;
      await this.page.screenshot({ path: screenshotPath, fullPage: true });
      console.log('📸 页面截图:', screenshotPath);
      
      // 查找并点击查询按钮
      console.log('\n🔍 查找查询按钮...');
      await this.clickQueryButton();
      
      // 等待数据加载
      console.log('\n⏳ 等待数据加载...');
      await this.page.waitForTimeout(5000);
      
      // 尝试提取页面数据
      const pageData = await this.extractPageData();
      
      return {
        city: '上海',
        success: this.interceptedData.length > 0,
        data: this.interceptedData,
        pageData: pageData
      };
      
    } catch (error) {
      console.error('\n❌ 爬取失败:', error.message);
      throw error;
    }
  }

  /**
   * 点击查询按钮
   */
  async clickQueryButton() {
    const buttonSelectors = [
      'button:has-text("查询")',
      'button:has-text("搜索")',
      'input[type="button"][value*="查询"]',
      'a:has-text("查询")',
      '#queryBtn',
      '.query-btn',
      'button.btn-search'
    ];
    
    for (const selector of buttonSelectors) {
      try {
        const button = await this.page.$(selector);
        if (button) {
          console.log(`   ✅ 找到按钮: ${selector}`);
          await button.click();
          console.log('   🖱️  已点击');
          await this.page.waitForTimeout(2000);
          return;
        }
      } catch (e) {
        // 继续尝试下一个选择器
      }
    }
    
    console.log('   ⚠️  未找到查询按钮，可能页面自动加载数据');
  }

  /**
   * 提取页面数据
   */
  async extractPageData() {
    try {
      // 尝试获取 #list_data 元素
      const listData = await this.page.$('#list_data');
      if (listData) {
        const text = await listData.textContent();
        console.log('\n📊 找到 #list_data 元素');
        console.log('   内容长度:', text.length);
        return { element: '#list_data', content: text };
      }
      
      // 尝试获取表格数据
      const table = await this.page.$('table');
      if (table) {
        const html = await table.innerHTML();
        console.log('\n📊 找到表格元素');
        console.log('   内容长度:', html.length);
        return { element: 'table', content: html };
      }
      
      console.log('\n⚠️  未能提取页面数据');
      return null;
      
    } catch (error) {
      console.log('\n⚠️  提取页面数据失败:', error.message);
      return null;
    }
  }

  /**
   * 爬取北京土地数据（待实现）
   */
  async scrapeBeijing() {
    console.log('\n📍 开始爬取：北京土地供应数据');
    // TODO: 实现北京土地数据爬取
    throw new Error('北京土地数据爬取尚未实现');
  }

  /**
   * 爬取广州土地数据（待实现）
   */
  async scrapeGuangzhou() {
    console.log('\n📍 开始爬取：广州土地供应数据');
    // TODO: 实现广州土地数据爬取
    throw new Error('广州土地数据爬取尚未实现');
  }

  /**
   * 爬取深圳土地数据（待实现）
   */
  async scrapeShenzhen() {
    console.log('\n📍 开始爬取：深圳土地供应数据');
    // TODO: 实现深圳土地数据爬取
    throw new Error('深圳土地数据爬取尚未实现');
  }

  /**
   * 保存数据到文件
   */
  saveData(data, filename) {
    const fs = require('fs');
    const path = require('path');
    
    // 确保目录存在
    const dir = path.dirname(filename);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    fs.writeFileSync(filename, JSON.stringify(data, null, 2), 'utf8');
    console.log('\n💾 数据已保存:', filename);
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
}

/**
 * 主函数 - 命令行接口
 */
async function main() {
  const args = process.argv.slice(2);
  const city = args[0] || 'shanghai';
  
  console.log('🏙️  土地数据爬虫');
  console.log('=' .repeat(60));
  console.log('目标城市:', city);
  console.log('=' .repeat(60));
  
  const scraper = new LandDataScraper({
    headless: false,
    screenshotPath: './screenshots'
  });
  
  try {
    // 初始化
    await scraper.init();
    
    // 根据城市选择爬取方法
    let result;
    switch (city.toLowerCase()) {
      case 'shanghai':
      case '上海':
        result = await scraper.scrapeShanghai();
        break;
      case 'beijing':
      case '北京':
        result = await scraper.scrapeBeijing();
        break;
      case 'guangzhou':
      case '广州':
        result = await scraper.scrapeGuangzhou();
        break;
      case 'shenzhen':
      case '深圳':
        result = await scraper.scrapeShenzhen();
        break;
      default:
        throw new Error(`不支持的城市: ${city}`);
    }
    
    // 保存结果
    if (result) {
      const filename = `./data/${city}_land_data.json`;
      scraper.saveData(result, filename);
      
      console.log('\n✅ 爬取完成!');
      console.log('   拦截到', result.data.length, '个请求/响应');
      console.log('   数据已保存:', filename);
    }
    
    // 保持浏览器打开
    console.log('\n⏸️  按 Ctrl+C 退出...');
    
  } catch (error) {
    console.error('\n❌ 错误:', error.message);
    await scraper.close();
    process.exit(1);
  }
}

// 如果直接运行
if (require.main === module) {
  main().catch(console.error);
}

module.exports = LandDataScraper;
