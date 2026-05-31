# 表单 · 处理模式

Voicebox 使用 **react-hook-form** + **Zod** 验证 + shadcn/ui `Form` 组件。表单 schema 同时定义验证规则和 TypeScript 类型。

## 技术栈

| 库 | 用途 |
|---|---|
| `react-hook-form` | 表单状态管理、提交处理 |
| `@hookform/resolvers` | Zod 集成 |
| `zod` | Schema 验证、类型推导 |
| `ui/form.tsx` | shadcn/ui 表单布局原语 |

## 基本模式

### 1. 定义 Schema

```tsx
import * as z from 'zod';
import { LANGUAGE_CODES, type LanguageCode } from '@/lib/constants/languages';

const generationSchema = z.object({
  text: z.string().min(1, 'Text is required').max(50000),
  language: z.enum(LANGUAGE_CODES as [LanguageCode, ...LanguageCode[]]),
  seed: z.number().int().optional(),
  temperature: z.number().min(0).max(2).optional(),
  topP: z.number().min(0).max(1).optional(),
  engine: z.enum(['indextts2']).optional(),
});

// 推导 TypeScript 类型
export type GenerationFormValues = z.infer<typeof generationSchema>;
```

### 2. 创建表单 Hook

```tsx
export function useGenerationForm(options: UseGenerationFormOptions = {}) {
  const { toast } = useToast();
  const generation = useGeneration();

  const form = useForm<GenerationFormValues>({
    resolver: zodResolver(generationSchema),
    defaultValues: {
      text: '',
      language: 'en',
      seed: undefined,
      temperature: 0.8,
      topP: 0.8,
      engine: 'indextts2',
      ...options.defaultValues,  // 允许外部覆盖默认值
    },
  });

  async function handleSubmit(data: GenerationFormValues): Promise<void> {
    try {
      const result = await generation.mutateAsync({
        profile_id: selectedProfileId,
        text: data.text,
        language: data.language,
        // ... 转换为 API 格式
      });

      // 提交成功后重置表单（保留部分字段）
      form.reset({
        text: '',
        language: data.language,
        engine: data.engine,
        // ... 保留用户偏好
      });

      options.onSuccess?.(result.id);
    } catch (error) {
      toast({
        title: 'Generation failed',
        description: error instanceof Error ? error.message : 'Failed to generate',
        variant: 'destructive',
      });
    }
  }

  return {
    form,
    handleSubmit,
    isPending: generation.isPending,
  };
}
```

### 3. 在组件中使用

```tsx
function GenerationPanel() {
  const { form, handleSubmit, isPending } = useGenerationForm();

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="text"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Text</FormLabel>
              <FormControl>
                <Textarea {...field} placeholder="Enter text to generate..." />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="language"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Language</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="zh">Chinese</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" disabled={isPending}>
          {isPending ? 'Generating...' : 'Generate'}
        </Button>
      </form>
    </Form>
  );
}
```

## Form 组件原语

shadcn/ui `Form` 组件提供一致的表单布局：

| 组件 | 用途 |
|---|---|
| `<Form {...form}>` | 表单上下文提供者，传递 form 实例 |
| `<FormField>` | 连接 react-hook-form 字段与 UI |
| `<FormItem>` | 字段容器（提供 spacing） |
| `<FormLabel>` | 标签（自动关联字段，显示错误状态） |
| `<FormControl>` | 包裹输入控件（传递 field props） |
| `<FormDescription>` | 字段描述文本 |
| `<FormMessage>` | 错误消息（自动显示验证错误） |

### FormField 模式

```tsx
<FormField
  control={form.control}    // react-hook-form control
  name="fieldName"          // schema 中的字段名
  render={({ field }) => (  // field 包含 value, onChange, onBlur 等
    <FormItem>
      <FormLabel>Label</FormLabel>
      <FormControl>
        <Input {...field} />
      </FormControl>
      <FormDescription>Optional description</FormDescription>
      <FormMessage />
    </FormItem>
  )}
/>
```

## 常见表单场景

### 文本输入

```tsx
<FormField
  control={form.control}
  name="text"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Text</FormLabel>
      <FormControl>
        <Textarea {...field} placeholder="Enter text..." />
      </FormControl>
      <FormMessage />
    </FormItem>
  )}
/>
```

### 下拉选择

```tsx
<FormField
  control={form.control}
  name="language"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Language</FormLabel>
      <Select onValueChange={field.onChange} defaultValue={field.value}>
        <FormControl>
          <SelectTrigger>
            <SelectValue placeholder="Select language" />
          </SelectTrigger>
        </FormControl>
        <SelectContent>
          {LANGUAGE_CODES.map((code) => (
            <SelectItem key={code} value={code}>
              {ALL_LANGUAGES[code]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <FormMessage />
    </FormItem>
  )}
/>
```

### 数字输入

```tsx
<FormField
  control={form.control}
  name="temperature"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Temperature</FormLabel>
      <FormControl>
        <Input
          type="number"
          step="0.1"
          min={0}
          max={2}
          {...field}
          onChange={(e) => field.onChange(parseFloat(e.target.value))}
        />
      </FormControl>
      <FormDescription>Controls randomness (0-2)</FormDescription>
      <FormMessage />
    </FormItem>
  )}
/>
```

### 滑块

```tsx
<FormField
  control={form.control}
  name="volume"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Volume: {field.value}%</FormLabel>
      <FormControl>
        <Slider
          min={0}
          max={100}
          step={1}
          value={[field.value]}
          onValueChange={([value]) => field.onChange(value)}
        />
      </FormControl>
      <FormMessage />
    </FormItem>
  )}
/>
```

### 复选框

```tsx
<FormField
  control={form.control}
  name="normalize"
  render={({ field }) => (
    <FormItem className="flex flex-row items-start space-x-3 space-y-0">
      <FormControl>
        <Checkbox
          checked={field.value}
          onCheckedChange={field.onChange}
        />
      </FormControl>
      <div className="space-y-1 leading-none">
        <FormLabel>Normalize Audio</FormLabel>
        <FormDescription>Apply audio normalization</FormDescription>
      </div>
    </FormItem>
  )}
/>
```

### 条件字段

```tsx
const useEmoText = form.watch('useEmoText');

{useEmoText && (
  <FormField
    control={form.control}
    name="emoText"
    render={({ field }) => (
      <FormItem>
        <FormLabel>Emotion Text</FormLabel>
        <FormControl>
          <Textarea {...field} />
        </FormControl>
        <FormMessage />
      </FormItem>
    )}
  />
)}
```

## Zod Schema 模式

### 基本验证

```tsx
const schema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  email: z.string().email('Invalid email'),
  age: z.number().int().min(0).max(150).optional(),
});
```

### 枚举

```tsx
// 字符串枚举
const engine = z.enum(['indextts2', 'chatterbox', 'kokoro']);

// 从常量推导
const language = z.enum(LANGUAGE_CODES as [LanguageCode, ...LanguageCode[]]);
```

### 数组

```tsx
const emoVector = z.array(z.number().min(0).max(1.4)).length(8);
const tags = z.array(z.string()).min(1).max(10);
```

### 联合类型

```tsx
const value = z.union([z.string(), z.number()]);
```

### 可选字段

```tsx
const schema = z.object({
  required: z.string(),
  optional: z.string().optional(),
  withDefault: z.string().default('default value'),
});
```

## 错误处理

### 表单级错误

```tsx
async function handleSubmit(data: FormValues) {
  try {
    await submitToApi(data);
  } catch (error) {
    // 设置表单级错误
    form.setError('root', {
      message: error instanceof Error ? error.message : 'Submission failed',
    });
  }
}
```

### 字段级错误

```tsx
form.setError('email', {
  type: 'manual',
  message: 'This email is already taken',
});
```

### 显示根错误

```tsx
{form.formState.errors.root && (
  <p className="text-sm text-destructive">
    {form.formState.errors.root.message}
  </p>
)}
```

## 表单状态

```tsx
const { isSubmitting, isDirty, isValid, errors } = form.formState;

<Button type="submit" disabled={isSubmitting || !isDirty}>
  {isSubmitting ? 'Submitting...' : 'Submit'}
</Button>
```

## 最佳实践

1. **Schema 即类型**：使用 `z.infer` 从 schema 推导 TypeScript 类型，不要手动定义接口。
2. **默认值在 hook 中**：表单默认值在自定义 hook 中定义，组件只关心渲染。
3. **转换在提交时**：表单使用 camelCase，API 使用 snake_case，转换在 `handleSubmit` 中完成。
4. **重置保留偏好**：提交成功后重置表单，但保留用户的偏好设置（如语言、引擎）。
5. **错误在 toast 中**：提交错误通过 `toast()` 显示，不依赖表单级错误。
6. **条件字段用 watch**：使用 `form.watch()` 控制条件字段的显示。
