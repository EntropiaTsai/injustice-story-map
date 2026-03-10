import type { VercelRequest, VercelResponse } from '@vercel/node';

interface ContributionData {
  storyId?: string;
  storyName?: string;
  victimName: string;
  location: string;
  year: string;
  articleLinks: string;
  videoLinks: string;
  additionalInfo: string;
  submitterEmail?: string;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse,
) {
  // 只接受 POST 請求
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const formData: ContributionData = req.body;
    
    // 驗證必填欄位
    if (!formData.victimName || !formData.location || !formData.year) {
      return res.status(400).json({ error: '請填寫必填欄位' });
    }

    // 產生唯一 ID
    const timestamp = Date.now();
    const contributionId = `contribution_${timestamp}`;
    
    // 轉換成固定格式的 JSON
    const jsonData = {
      id: contributionId,
      timestamp: new Date().toISOString(),
      type: formData.storyId ? 'supplement' : 'new_story',
      storyId: formData.storyId || null,
      storyName: formData.storyName || '',
      victimName: formData.victimName,
      location: formData.location,
      year: formData.year,
      articleLinks: formData.articleLinks
        .split('\n')
        .map(link => link.trim())
        .filter(link => link.length > 0),
      videoLinks: formData.videoLinks
        .split('\n')
        .map(link => link.trim())
        .filter(link => link.length > 0),
      additionalInfo: formData.additionalInfo,
      submitterEmail: formData.submitterEmail || '',
      status: 'pending',
      createdAt: new Date().toISOString(),
    };

    // 使用 GitHub API 儲存檔案
    const githubToken = process.env.GITHUB_TOKEN;
    const githubRepo = process.env.GITHUB_REPO; // 格式: owner/repo
    
    if (!githubToken || !githubRepo) {
      console.error('缺少 GitHub 環境變數');
      // 暫時先記錄到 console，未來可以改用其他方式
      console.log('收到投稿:', jsonData);
      return res.status(200).json({ 
        success: true, 
        message: '感謝您的貢獻！資料已記錄。',
        id: contributionId 
      });
    }

    // 呼叫 GitHub API 建立檔案
    const [owner, repo] = githubRepo.split('/');
    const filePath = `contributions/${contributionId}.json`;
    const content = Buffer.from(JSON.stringify(jsonData, null, 2)).toString('base64');

    const githubResponse = await fetch(
      `https://api.github.com/repos/${owner}/${repo}/contents/${filePath}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: `feat: 新增投稿 ${contributionId}`,
          content: content,
          branch: 'main',
        }),
      }
    );

    if (!githubResponse.ok) {
      const errorData = await githubResponse.json();
      console.error('GitHub API 錯誤:', errorData);
      throw new Error('無法儲存到 GitHub');
    }

    return res.status(200).json({
      success: true,
      message: '感謝您的貢獻！我們會審核並處理您提供的資料。',
      id: contributionId,
    });

  } catch (error) {
    console.error('處理投稿時發生錯誤:', error);
    return res.status(500).json({
      error: '處理投稿時發生錯誤，請稍後再試',
    });
  }
}
