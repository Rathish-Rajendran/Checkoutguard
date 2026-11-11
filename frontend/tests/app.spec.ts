import{test,expect}from'@playwright/test';
test('merchant investigates a lost response, inspects evidence and replays safely',async({page})=>{
 await page.goto('/');await page.getByLabel('Merchant API key').fill('local-demo-key-change-me');await page.getByRole('button',{name:'Open workspace'}).click();
 await page.getByRole('button',{name:'Simulate interrupted checkout'}).click();
 await expect(page.locator('.card-title').filter({hasText:'Flight Recorder'})).toBeVisible();
 await expect(page.getByText('Payment Truth: UNKNOWN')).toBeVisible();
 await page.getByRole('button',{name:'Reconcile now'}).click();await expect(page.getByText('Payment Truth: CONFIRMED')).toBeVisible();
 await page.getByRole('button',{name:'Investigate incident'}).click();await expect(page.getByLabel('Customer reply draft')).toHaveValue(/CONFIRMED/);
 await page.getByRole('button').filter({hasText:'source record · inspect evidence'}).first().click();
 await expect(page.locator('pre')).toContainText('COMPLETED');
 await page.screenshot({path:'/tmp/checkoutguard-incident.png',fullPage:true});
 await page.getByRole('button',{name:'Replay Lab',exact:true}).click();await page.getByRole('button',{name:'Run simulation'}).click();
 await expect(page.getByText('All assertions passed')).toBeVisible();
 await page.screenshot({path:'/tmp/checkoutguard-replay.png',fullPage:true});
});
test('buyer sees minimal private truth and responsive checkout works',async({page})=>{
 await page.goto('/');await page.getByLabel('Merchant API key').fill('local-demo-key-change-me');await page.getByRole('button',{name:'Open workspace'}).click();
 await page.getByRole('button',{name:'Demo checkout',exact:true}).click();await page.getByRole('button',{name:'Start simulated checkout'}).click();
 await page.getByRole('button',{name:'Capture approved order'}).click();await page.getByRole('link',{name:'Open private payment status'}).click();
 await expect(page.getByRole('heading',{name:'Your payment is confirmed.'})).toBeVisible();
 await page.setViewportSize({width:390,height:844});await expect(page.getByRole('heading',{name:'Your payment is confirmed.'})).toBeVisible();
 await page.screenshot({path:'/tmp/checkoutguard-buyer-mobile.png',fullPage:true});
});
