const { chromium } = require('playwright');

/**
 * 上海土地数据爬虫 - 拦截真实 API 请求版本
 * 核心思路：让页面自己生成 token 并发送请求，我们直接拦截
 */
async function scrapeShanghai() {
  console.log('🚀 启动上海土地数据爬虫...');
  
  const browser = await chromium.launch({
    headless: false,  // 显示浏览器，方便调试
    slowMo: 100,     // 放慢操作，避免被检测
    args: [
      '--disable-blink-features=AutomationControlled',
      '--disable-dev-shm-usage',
      '--no-sandbox'
    ]
  });
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1920, height: 1080 }
  });
  
  const page = await context.newPage();
  
  // 存储拦截到的 API 数据
  let interceptedRequests = [];
  let interceptedResponses = [];
  
  // 监听所有请求
  page.on('request', async (request) => {
    const url = request.url();
    
    // 拦截包含 listForPage 或 land 的请求
    if (url.includes('listForPage') || url.includes('land') || url.includes('ghsl')) {
      console.log('\n📡 [请求拦截]', url);
      console.log('   方法:', request.method());
      
      const postData = request.postData();
      if (postData) {
        console.log('   请求体:', postData.substring(0, 500));
      }
      
      interceptedRequests.push({
        url: url,
        method: request.method(),
        headers: request.headers(),
        postData: postData,
        timestamp: new Date().toISOString()
      });
    }
  });
  
  // 监听所有响应
  page.on('response', async (response) => {
    const url = response.url();
    
    // 拦截包含 listForPage 或 land 的响应
    if (url.includes('listForPage') || url.includes('land') || url.includes('ghsl')) {
      console.log('\n✅ [响应拦截]', url);
      console.log('   状态码:', response.status());
      
      try {
        const contentType = response.headers()['content-type'] || '';
        
        if (contentType.includes('json') || url.includes('listForPage')) {
          const text = await response.text();
          console.log('   响应长度:', text.length);
          console.log('   响应预览:', text.substring(0, 200));
          
          interceptedResponses.push({
            url: url,
            status: response.status(),
            headers: response.headers(),
            body: text,
            timestamp: new Date().toISOString()
          });
          
          // 尝试解析 JSON
          if (text.startsWith('{') || text.startsWith('[')) {
            try {
              const json = JSON.parse(text);
              console.log('   ✅ JSON 解析成功!');
              console.log('   数据键:', Object.keys(json));
            } catch (e) {
              console.log('   ⚠️  JSON 解析失败:', e.message);
            }
          }
        }
      } catch (e) {
        console.log('   ❌ 读取响应失败:', e.message);
      }
    }
  });
  
  try {
    // 访问上海土地供应页面
    const url = 'https://ghzyj.sh.gov.cn/land_ghsl/';
    console.log('\n🌐 正在访问:', url);
    
    await page.goto(url, { 
      waitUntil: 'networkidle',
      timeout: 60000 
    });
    
    console.log('✅ 页面加载完成');
    
    // 等待页面完全渲染
    await page.waitForTimeout(3000);
    
    // 截图
    await page.screenshot({ path: 'shanghai_land_page.png', fullPage: true });
    console.log('📸 页面截图已保存: shanghai_land_page.png');
    
    // 打印页面标题
    const title = await page.title();
    console.log('📄 页面标题:', title);
    
    // 查找可能的数据加载按钮或链接
    console.log('\n🔍 查找数据加载元素...');
    
    // 尝试查找并点击"查询"按钮
    const buttons = await page.$$('button, input[type="button"], a');
    console.log(`   找到 ${buttons.length} 个按钮/链接`);
    
    for (let i = 0; i < Math.min(buttons.length, 10); i++) {
      const text = await buttons[i].textContent().catch(() => '');
      if (text.includes('查询') || text.includes('搜索') || text.includes('提交')) {
        console.log(`   ✅ 找到按钮: ${text}`);
        console.log('   🖱️  尝试点击...');
        await buttons[i].click().catch(e => console.log('   点击失败:', e.message));
        await page.waitForTimeout(2000);
        break;
      }
    }
    
    // 等待可能的 AJAX 请求
    console.log('\n⏳ 等待数据加载 (5秒)...');
    await page.waitForTimeout(5000);
    
    // 检查是否拦截到数据
    if (interceptedResponses.length > 0) {
      console.log('\n✅ 成功拦截到', interceptedResponses.length, '个响应!');
      
      // 保存第一个响应的数据
      const data = interceptedResponses[0];
      const fs = require('fs');
      fs.writeFileSync(
        'shanghai_land_api_response.json',
        JSON.stringify(data, null, 2),
        'utf8'
      );
      console.log('💾 数据已保存: shanghai_land_api_response.json');
      
      return data;
    } else {
      console.log('\n⚠️  未能拦截到 API 响应');
      console.log('   可能的原因:');
      console.log('   1. 页面没有自动加载数据');
      console.log('   2. 需要手动触发查询');
      console.log('   3. URL 不正确');
      
      // 打印页面 HTML 结构的一部分
      const bodyHTML = await page.content();
      console.log('\n📄 页面 HTML 长度:', bodyHTML.length);
      
      return null;
    }
    
  } catch (error) {
    console.error('\n❌ 错误:', error.message);
    throw error;
  } finally {
    // 保持浏览器打开，让用户查看
    console.log('\n⏸️  浏览器保持打开状态，按 Ctrl+C 退出...');
    // 不自动关闭浏览器
    // await browser.close();
  }
}

// 运行
scrapeShanghai().catch(console.error);
