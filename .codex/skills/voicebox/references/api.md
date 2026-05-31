# API 层 · 数据获取模式

Voicebox 前端有两层 API：手写 `ApiClient`（实际使用）+ 自动生成的 OpenAPI 类型（参考用）。所有数据获取通过 TanStack Query hooks 包装。

## 架构概览

```
组件 → TanStack Query Hook → ApiClient → fetch() → FastAPI 后端
                ↕
         React Query Cache
                ↕
         Zustand Store (客户端状态)
```

## ApiClient

`lib/api/client.ts` 中的单例类，使用 `fetch()` 直接调用后端：

```tsx
import { useServerStore } from '@/stores/serverStore';
import type { VoiceProfileResponse, VoiceProfileCreate } from './types';

class ApiClient {
  // 运行时从 store 读取服务器 URL
  private getBaseUrl(): string {
    return useServerStore.getState().serverUrl;
  }

  // 通用请求方法
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.getBaseUrl()}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      throw new Error(formatErrorDetail(error.detail, `HTTP error! status: ${response.status}`));
    }

    return response.json();
  }

  // 具体 API 方法
  async listProfiles(): Promise<VoiceProfileResponse[]> {
    return this.request('/profiles');
  }

  async getProfile(profileId: string): Promise<VoiceProfileResponse> {
    return this.request(`/profiles/${profileId}`);
  }

  async createProfile(data: VoiceProfileCreate): Promise<VoiceProfileResponse> {
    return this.request('/profiles', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteProfile(profileId: string): Promise<void> {
    return this.request(`/profiles/${profileId}`, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient();
```

### 关键特性

1. **运行时读取 URL**：从 `useServerStore.getState()` 读取，不从构造函数。
2. **统一错误处理**：`formatErrorDetail()` 解析后端错误格式。
3. **文件上传**：使用 `FormData` + 直接 `fetch()`。
4. **SSE URL**：返回 URL 字符串，由调用方创建 `EventSource`。
5. **音频 URL**：返回可直接用于 `<audio>` 的 URL。

### 文件上传模式

```tsx
async addProfileSample(
  profileId: string,
  file: File,
  referenceText: string,
): Promise<ProfileSampleResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('reference_text', referenceText);

  const url = `${this.getBaseUrl()}/profiles/${profileId}/samples`;
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    // 不要设置 Content-Type，让浏览器自动设置 boundary
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(formatErrorDetail(error.detail, 'Upload failed'));
  }

  return response.json();
}
```

### SSE URL 模式

```tsx
getGenerationStatusUrl(generationId: string): string {
  return `${this.getBaseUrl()}/generate/${generationId}/status`;
}

getAudioUrl(generationId: string): string {
  return `${this.getBaseUrl()}/audio/${generationId}`;
}
```

## 类型定义

`lib/api/types.ts` 是 API 类型的唯一真实来源（手动维护，snake_case 匹配 Python 后端）：

```tsx
export interface VoiceProfileResponse {
  id: string;
  name: string;
  description?: string;
  language: string;
  avatar_path?: string;
  effects_chain?: EffectConfig[];
  generation_count: number;
  sample_count: number;
  created_at: string;
  updated_at: string;
}

export interface GenerationRequest {
  profile_id: string;
  text: string;
  language: LanguageCode;
  engine?: 'indextts2';
  // ... 其他参数
}

export interface GenerationResponse {
  id: string;
  status: string;
  // ...
}
```

### 命名约定

- API 类型使用 **snake_case**（匹配 Python 后端）
- 前端组件/变量使用 **camelCase**
- 转换在 hook 层完成（如果需要）

## TanStack Query Hooks

每个领域一个文件在 `lib/hooks/` 中，使用 TanStack Query 包装 `apiClient` 调用。

### 查询 Hook

```tsx
// lib/hooks/useProfiles.ts
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useProfiles() {
  return useQuery({
    queryKey: ['profiles'],
    queryFn: () => apiClient.listProfiles(),
  });
}

export function useProfile(profileId: string) {
  return useQuery({
    queryKey: ['profiles', profileId],
    queryFn: () => apiClient.getProfile(profileId),
    enabled: !!profileId,  // 条件查询
  });
}
```

### Mutation Hook

```tsx
export function useCreateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: VoiceProfileCreate) => apiClient.createProfile(data),
    onSuccess: () => {
      // 成功后使缓存失效，触发重新获取
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });
}
```

### 带参数的 Mutation

```tsx
export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ profileId, data }: { profileId: string; data: VoiceProfileCreate }) =>
      apiClient.updateProfile(profileId, data),
    onSuccess: (_, variables) => {
      // 使列表和单个详情缓存都失效
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      queryClient.invalidateQueries({
        queryKey: ['profiles', variables.profileId],
      });
    },
  });
}
```

### 乐观更新

```tsx
export function useGenerationSettings() {
  const queryClient = useQueryClient();
  const KEY = ['generation-settings'];

  return useMutation({
    mutationFn: (patch: GenerationSettingsUpdate) =>
      apiClient.updateGenerationSettings(patch),

    // 乐观更新：立即更新缓存
    onMutate: async (patch) => {
      await queryClient.cancelQueries({ queryKey: KEY });
      const previous = queryClient.getQueryData(KEY);
      queryClient.setQueryData(KEY, (old) => ({ ...old, ...patch }));
      return { previous };
    },

    // 失败时回滚
    onError: (_err, _patch, ctx) => {
      queryClient.setQueryData(KEY, ctx?.previous);
    },

    // 成功时用服务器响应覆盖
    onSettled: (data) => {
      if (data) queryClient.setQueryData(KEY, data);
    },
  });
}
```

### SSE 订阅 Hook

```tsx
// lib/hooks/useGenerationProgress.ts
export function useGenerationProgress() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const pendingIds = useGenerationStore((s) => s.pendingGenerationIds);
  const removePendingGeneration = useGenerationStore((s) => s.removePendingGeneration);

  useEffect(() => {
    for (const id of pendingIds) {
      const url = apiClient.getGenerationStatusUrl(id);
      const source = new EventSource(url);

      source.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.status === 'completed') {
          source.close();
          removePendingGeneration(id);
          queryClient.refetchQueries({ queryKey: ['history'] });
          // 自动播放逻辑...
        } else if (data.status === 'failed') {
          source.close();
          removePendingGeneration(id);
          toast({ title: 'Generation failed', variant: 'destructive' });
        }
      };

      source.onerror = () => {
        source.close();
        removePendingGeneration(id);
      };
    }
  }, [pendingIds, removePendingGeneration, queryClient, toast]);
}
```

## Query Client 配置

```tsx
// lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 分钟内认为数据新鲜
      gcTime: 10 * 60 * 1000,        // 10 分钟后清理未使用的缓存
      retry: 1,                       // 失败重试 1 次
      refetchOnWindowFocus: false,    // 窗口聚焦时不自动刷新
    },
  },
});
```

## 添加新的 API 方法

### 步骤

1. **添加类型**：在 `lib/api/types.ts` 添加请求/响应接口

```tsx
export interface MyNewResponse {
  id: string;
  name: string;
  // ...
}
```

2. **添加 ApiClient 方法**：在 `lib/api/client.ts`

```tsx
async listMyNew(): Promise<MyNewResponse[]> {
  return this.request('/my-new');
}

async createMyNew(data: MyNewCreate): Promise<MyNewResponse> {
  return this.request('/my-new', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

3. **创建 Query Hook**：在 `lib/hooks/useMyNew.ts`

```tsx
export function useMyNewList() {
  return useQuery({
    queryKey: ['my-new'],
    queryFn: () => apiClient.listMyNew(),
  });
}

export function useCreateMyNew() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MyNewCreate) => apiClient.createMyNew(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-new'] });
    },
  });
}
```

4. **在组件中使用**

```tsx
function MyComponent() {
  const { data: items, isLoading } = useMyNewList();
  const createMutation = useCreateMyNew();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {items?.map((item) => <div key={item.id}>{item.name}</div>)}
      <Button onClick={() => createMutation.mutate({ name: 'New' })}>
        Create
      </Button>
    </div>
  );
}
```

## Query Key 命名约定

| 领域 | Key | 说明 |
|---|---|---|
| Profiles | `['profiles']` | 列表 |
| Profile 详情 | `['profiles', id]` | 单个 |
| Profile 样本 | `['profiles', id, 'samples']` | 嵌套资源 |
| History | `['history']` | 生成历史 |
| Stories | `['stories']` | 故事列表 |
| Story 详情 | `['stories', id]` | 单个 |
| Settings | `['generation-settings']` | 生成设置 |
| Models | `['models']` | 模型状态 |
| Effects | `['effects', 'presets']` | 音效预设 |
| Audio Library | `['audio-library']` | 音频库 |
