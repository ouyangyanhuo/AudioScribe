import { zodResolver } from '@hookform/resolvers/zod';
import { Library, Mic, Upload } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { useAudioPlayer } from '@/lib/hooks/useAudioPlayer';
import { useAudioRecording } from '@/lib/hooks/useAudioRecording';
import { useUseAudioLibraryAsSample } from '@/lib/hooks/useAudioLibrary';
import { useAddSample } from '@/lib/hooks/useProfiles';
import { AudioLibraryBrowser } from '@/components/AudioLibrary/AudioLibraryBrowser';
import { AudioSampleRecording } from './AudioSampleRecording';
import { AudioSampleUpload } from './AudioSampleUpload';

const sampleSchema = z.object({
  file: z.instanceof(File, { message: 'Please select an audio file' }),
  referenceText: z
    .string()
    .min(1, 'Reference text is required')
    .max(1000, 'Reference text must be less than 1000 characters'),
});

type SampleFormValues = z.infer<typeof sampleSchema>;

interface SampleUploadProps {
  profileId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SampleUpload({ profileId, open, onOpenChange }: SampleUploadProps) {
  const addSample = useAddSample();
  const useLibrarySample = useUseAudioLibraryAsSample();
  const { toast } = useToast();
  const [mode, setMode] = useState<'upload' | 'record' | 'library'>('upload');
  const { isPlaying, playPause, cleanup: cleanupAudio } = useAudioPlayer();

  const form = useForm<SampleFormValues>({
    resolver: zodResolver(sampleSchema),
    defaultValues: {
      referenceText: '',
    },
  });

  const selectedFile = form.watch('file');

  const {
    isRecording,
    duration,
    error: recordingError,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useAudioRecording({
    maxDurationSeconds: 29,
    onRecordingComplete: (blob, recordedDuration) => {
      // Convert blob to File object
      const file = new File([blob], `recording-${Date.now()}.webm`, {
        type: blob.type || 'audio/webm',
      }) as File & { recordedDuration?: number };
      // Store the actual recorded duration to bypass metadata reading issues on Windows
      if (recordedDuration !== undefined) {
        file.recordedDuration = recordedDuration;
      }
      form.setValue('file', file, { shouldValidate: true });
      toast({
        title: 'Recording complete',
        description: 'Audio has been recorded successfully.',
      });
    },
  });

  // Show recording errors
  useEffect(() => {
    if (recordingError) {
      toast({
        title: 'Recording error',
        description: recordingError,
        variant: 'destructive',
      });
    }
  }, [recordingError, toast]);

  async function onSubmit(data: SampleFormValues) {
    try {
      await addSample.mutateAsync({
        profileId,
        file: data.file,
        referenceText: data.referenceText,
      });

      toast({
        title: 'Sample added',
        description: 'Audio sample has been added successfully.',
      });

      handleOpenChange(false);
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to add sample',
        variant: 'destructive',
      });
    }
  }

  async function handleLibrarySelect(itemId: string) {
    const referenceText = form.getValues('referenceText')?.trim();
    if (!referenceText) {
      form.setError('referenceText', {
        type: 'manual',
        message: 'Reference text is required before selecting from the library',
      });
      return;
    }

    try {
      await useLibrarySample.mutateAsync({ itemId, profileId, referenceText });
      toast({
        title: 'Sample added',
        description: 'Audio library item has been added successfully.',
      });
      handleOpenChange(false);
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to add library sample',
        variant: 'destructive',
      });
    }
  }

  function handleOpenChange(newOpen: boolean) {
    if (!newOpen) {
      form.reset();
      setMode('upload');
      if (isRecording) {
        cancelRecording();
      }
      cleanupAudio();
    }
    onOpenChange(newOpen);
  }

  function handleCancelRecording() {
    cancelRecording();
    form.resetField('file');
    cleanupAudio();
  }

  function handlePlayPause() {
    const file = form.getValues('file');
    playPause(file);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Audio Sample</DialogTitle>
          <DialogDescription>
            Upload an audio file and provide the reference text that matches the audio.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <Tabs value={mode} onValueChange={(v) => setMode(v as 'upload' | 'record' | 'library')}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="upload" className="flex items-center gap-2">
                  <Upload className="h-4 w-4 shrink-0" />
                  Upload
                </TabsTrigger>
                <TabsTrigger value="record" className="flex items-center gap-2">
                  <Mic className="h-4 w-4 shrink-0" />
                  Record
                </TabsTrigger>
                <TabsTrigger value="library" className="flex items-center gap-2">
                  <Library className="h-4 w-4 shrink-0" />
                  Library
                </TabsTrigger>
              </TabsList>

              <TabsContent value="upload" className="space-y-4">
                <FormField
                  control={form.control}
                  name="file"
                  render={({ field: { onChange, name } }) => (
                    <AudioSampleUpload
                      file={selectedFile}
                      onFileChange={onChange}
                      onPlayPause={handlePlayPause}
                      isPlaying={isPlaying}
                      fieldName={name}
                    />
                  )}
                />
              </TabsContent>

              <TabsContent value="library" className="space-y-4">
                <AudioLibraryBrowser onSelect={(item) => handleLibrarySelect(item.id)} />
              </TabsContent>

              <TabsContent value="record" className="space-y-4">
                <FormField
                  control={form.control}
                  name="file"
                  render={() => (
                    <AudioSampleRecording
                      file={selectedFile}
                      isRecording={isRecording}
                      duration={duration}
                      onStart={startRecording}
                      onStop={stopRecording}
                      onCancel={handleCancelRecording}
                      onPlayPause={handlePlayPause}
                      isPlaying={isPlaying}
                    />
                  )}
                />
              </TabsContent>
            </Tabs>

            <FormField
              control={form.control}
              name="referenceText"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Reference Text</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Enter the exact text spoken in the audio..."
                      className="min-h-[100px]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex gap-2 justify-end">
              <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={addSample.isPending}>
                {addSample.isPending ? 'Uploading...' : 'Add Sample'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
