# 使用者投稿資料

此資料夾用於儲存使用者透過網站提交的故事投稿。

## JSON 格式說明

每個投稿會以 JSON 檔案儲存，檔名格式為：`contribution_<timestamp>.json`

### 欄位說明

```json
{
  "id": "contribution_1710123456789",
  "timestamp": "2026-03-11T01:30:00.000Z",
  "type": "new_story",  // "new_story" 或 "supplement"
  "storyId": null,  // 如果是補充現有故事，會有 story ID
  "storyName": "",
  "victimName": "受難者姓名",
  "location": "地點",
  "year": "年代",
  "articleLinks": ["文章連結1", "文章連結2"],
  "videoLinks": ["影片連結1"],
  "additionalInfo": "補充說明",
  "submitterEmail": "投稿者信箱（選填）",
  "status": "pending",  // pending / reviewed / approved / rejected
  "createdAt": "2026-03-11T01:30:00.000Z"
}
```

## 處理流程

1. 使用者在網站提交表單
2. API 自動產生 JSON 並儲存到此資料夾
3. 管理員定期檢視新投稿
4. 審核通過後，整合至 `src/data/stories.ts`
5. 更新投稿狀態為 `approved`

## 注意事項

- 所有投稿內容必須基於可驗證的官方資料來源
- 不接受個人推論或情感描述
- 審核時需確認提供的連結有效且可信
