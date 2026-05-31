import { zodResolver } from '@hookform/resolvers/zod';
import { Edit2, Library, Mic, Upload, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import * as z from 'zod';
import { AudioLibraryBrowser } from '@/components/AudioLibrary/AudioLibraryBrowser';
import { EffectsChainEditor } from '@/components/Effects/EffectsChainEditor';
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
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { apiClient } from '@/lib/api/client';
import type { EffectConfig } from '@/lib/api/types';
import { LANGUAGE_CODES, LANGUAGE_OPTIONS, type LanguageCode } from '@/lib/constants/languages';
import { useAudioPlayer } from '@/lib/hooks/useAudioPlayer';
import { useAudioRecording } from '@/lib/hooks/useAudioRecording';
import { useUseAudioLibraryAsSample } from '@/lib/hooks/useAudioLibrary';
import {
  useAddSample,
  useCreateProfile,
  useDeleteAvatar,
  useDeleteProfile,
  useProfile,
  useUpdateProfile,
  useUploadAvatar,
} from '@/lib/hooks/useProfiles';
import { formatAudioDuration, getAudioDuration } from '@/lib/utils/audio';
import { useServerStore } from '@/stores/serverStore';
import { useUIStore } from '@/stores/uiStore';
import { AudioSampleRecording } from './AudioSampleRecording';
import { AudioSampleUpload } from './AudioSampleUpload';
import { SampleList } from './SampleList';

const MAX_AUDIO_DURATION_SECONDS = 30;

function makeProfileSchema(t: (key: string) => string) {
  return z
    .object({
      name: z.string().min(1, t('profileForm.validation.nameRequired')).max(100),
      description: z.string().max(500).optional(),
      language: z.enum(LANGUAGE_CODES as [LanguageCode, ...LanguageCode[]]),
      sampleFile: z.instanceof(File).optional(),
      referenceText: z.string().max(1000).optional(),
      avatarFile: z.instanceof(File).optional(),
    })
    .refine(
      (data) =>
        !data.sampleFile || !!data.referenceText?.trim(),
      {
        message: t('profileForm.validation.referenceRequired'),
        path: ['referenceText'],
      },
    );
}

type ProfileFormValues = {
  name: string;
  description?: string;
  language: LanguageCode;
  sampleFile?: File;
  referenceText?: string;
  avatarFile?: File;
};

export function ProfileForm() {
  const { t } = useTranslation();
  const open = useUIStore((state) => state.profileDialogOpen);
  const setOpen = useUIStore((state) => state.setProfileDialogOpen);
  const editingProfileId = useUIStore((state) => state.editingProfileId);
  const setEditingProfileId = useUIStore((state) => state.setEditingProfileId);
  const { data: editingProfile } = useProfile(editingProfileId || '');
  const createProfile = useCreateProfile();
  const updateProfile = useUpdateProfile();
  const addSample = useAddSample();
  const useLibrarySample = useUseAudioLibraryAsSample();
  const deleteProfile = useDeleteProfile();
  const uploadAvatar = useUploadAvatar();
  const deleteAvatar = useDeleteAvatar();
  const { toast } = useToast();
  const serverUrl = useServerStore((state) => state.serverUrl);
  const [sampleMode, setSampleMode] = useState<'upload' | 'record' | 'library'>('record');
  const [isValidatingAudio, setIsValidatingAudio] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [profileEffectsChain, setProfileEffectsChain] = useState<EffectConfig[]>([]);
  const [effectsDirty, setEffectsDirty] = useState(false);
  const avatarInputRef = useRef<HTMLInputElement>(null);
  const { isPlaying, playPause, cleanup: cleanupAudio } = useAudioPlayer();

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(makeProfileSchema(t)),
    defaultValues: {
      name: '',
      description: '',
      language: 'en',
      referenceText: '',
    },
  });

  const selectedFile = form.watch('sampleFile');
  const selectedAvatarFile = form.watch('avatarFile');

  useEffect(() => {
    if (!selectedFile) {
      form.clearErrors('sampleFile');
      return;
    }

    setIsValidatingAudio(true);
    getAudioDuration(selectedFile as File & { recordedDuration?: number })
      .then((duration) => {
        if (duration > MAX_AUDIO_DURATION_SECONDS) {
          form.setError('sampleFile', {
            type: 'manual',
            message: t('profileForm.validation.audioTooLong', {
              duration: formatAudioDuration(duration),
              max: formatAudioDuration(MAX_AUDIO_DURATION_SECONDS),
            }),
          });
        } else {
          form.clearErrors('sampleFile');
        }
      })
      .catch(() => {
        form.setError('sampleFile', {
          type: 'manual',
          message: t('profileForm.validation.audioFailed'),
        });
      })
      .finally(() => setIsValidatingAudio(false));
  }, [selectedFile, form, t]);

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
      const file = new File([blob], `recording-${Date.now()}.webm`, {
        type: blob.type || 'audio/webm',
      }) as File & { recordedDuration?: number };
      file.recordedDuration = recordedDuration;
      form.setValue('sampleFile', file, { shouldValidate: true });
      toast({
        title: t('profileForm.toast.recordingComplete'),
        description: t('profileForm.toast.recordingCompleteDescription'),
      });
    },
  });

  useEffect(() => {
    if (recordingError) {
      toast({
        title: t('profileForm.toast.recordingError'),
        description: recordingError,
        variant: 'destructive',
      });
    }
  }, [recordingError, toast, t]);

  useEffect(() => {
    if (selectedAvatarFile instanceof File) {
      const url = URL.createObjectURL(selectedAvatarFile);
      setAvatarPreview(url);
      return () => URL.revokeObjectURL(url);
    }
    if (editingProfile?.avatar_path) {
      setAvatarPreview(`${serverUrl}/profiles/${editingProfile.id}/avatar`);
      return;
    }
    setAvatarPreview(null);
  }, [selectedAvatarFile, editingProfile, serverUrl]);

  useEffect(() => {
    if (editingProfile) {
      form.reset({
        name: editingProfile.name,
        description: editingProfile.description || '',
        language: editingProfile.language as LanguageCode,
        sampleFile: undefined,
        referenceText: '',
        avatarFile: undefined,
      });
      setProfileEffectsChain(editingProfile.effects_chain ?? []);
      setEffectsDirty(false);
    } else if (!open) {
      form.reset({
        name: '',
        description: '',
        language: 'en',
        sampleFile: undefined,
        referenceText: '',
        avatarFile: undefined,
      });
      setSampleMode('record');
      setAvatarPreview(null);
      setProfileEffectsChain([]);
      setEffectsDirty(false);
    }
  }, [editingProfile, open, form]);

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      if (isRecording) cancelRecording();
      cleanupAudio();
      setEditingProfileId(null);
    }
    setOpen(nextOpen);
  }

  function handlePlayPause() {
    playPause(form.getValues('sampleFile'));
  }

  function handleCancelRecording() {
    cancelRecording();
    form.resetField('sampleFile');
    cleanupAudio();
  }

  function handleAvatarFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      toast({
        title: t('profileForm.toast.invalidFile'),
        description: t('profileForm.toast.invalidImageFormat'),
        variant: 'destructive',
      });
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast({
        title: t('profileForm.toast.fileTooLarge'),
        description: t('profileForm.toast.imageTooLargeDescription'),
        variant: 'destructive',
      });
      return;
    }
    form.setValue('avatarFile', file);
  }

  async function handleRemoveAvatar() {
    if (editingProfileId && editingProfile?.avatar_path) {
      try {
        await deleteAvatar.mutateAsync(editingProfileId);
      } catch (error) {
        toast({
          title: t('profileForm.toast.avatarRemoveFailed'),
          description: error instanceof Error ? error.message : t('common.unknownError'),
          variant: 'destructive',
        });
      }
    }
    form.setValue('avatarFile', undefined);
    setAvatarPreview(null);
    if (avatarInputRef.current) avatarInputRef.current.value = '';
  }

  async function handleLibrarySelect(itemId: string) {
    const referenceText = form.getValues('referenceText')?.trim();
    if (!editingProfileId) {
      toast({
        title: 'Create the profile first',
        description: 'Library samples can be attached after the profile exists.',
        variant: 'destructive',
      });
      return;
    }
    if (!referenceText) {
      form.setError('referenceText', {
        type: 'manual',
        message: t('profileForm.validation.referenceRequired'),
      });
      return;
    }
    await useLibrarySample.mutateAsync({ itemId, profileId: editingProfileId, referenceText });
    toast({
      title: t('sampleUpload.sampleAdded', { defaultValue: 'Sample added' }),
      description: t('sampleUpload.librarySampleAdded', {
        defaultValue: 'Audio library item has been added successfully.',
      }),
    });
  }

  async function saveAvatar(profileId: string, avatarFile?: File) {
    if (!avatarFile) return;
    await uploadAvatar.mutateAsync({ profileId, file: avatarFile });
  }

  async function saveEffects(profileId: string) {
    if (!effectsDirty) return;
    await apiClient.updateProfileEffects(
      profileId,
      profileEffectsChain.length > 0 ? profileEffectsChain : null,
    );
  }

  async function onSubmit(data: ProfileFormValues) {
    try {
      if (editingProfileId) {
        await updateProfile.mutateAsync({
          profileId: editingProfileId,
          data: {
            name: data.name,
            description: data.description,
            language: data.language,
          },
        });
        await saveAvatar(editingProfileId, data.avatarFile);
        await saveEffects(editingProfileId);
        toast({
          title: t('profileForm.toast.voiceUpdated'),
          description: t('profileForm.toast.voiceUpdatedDescription', { name: data.name }),
        });
      } else {
        const profile = await createProfile.mutateAsync({
          name: data.name,
          description: data.description,
          language: data.language,
        });
        await saveAvatar(profile.id, data.avatarFile);
        if (data.sampleFile && data.referenceText?.trim()) {
          await addSample.mutateAsync({
            profileId: profile.id,
            file: data.sampleFile,
            referenceText: data.referenceText.trim(),
          });
        }
        toast({
          title: t('profileForm.toast.voiceCreated'),
          description: t('profileForm.toast.voiceCreatedDescription', { name: data.name }),
        });
      }
      handleOpenChange(false);
    } catch (error) {
      toast({
        title: t('profileForm.toast.saveFailed', { defaultValue: 'Save failed' }),
        description: error instanceof Error ? error.message : t('common.unknownError'),
        variant: 'destructive',
      });
    }
  }

  async function handleDelete() {
    if (!editingProfileId || !editingProfile) return;
    if (!window.confirm(t('profileForm.confirmDelete', { name: editingProfile.name }))) return;
    await deleteProfile.mutateAsync(editingProfileId);
    handleOpenChange(false);
  }

  const savePending =
    createProfile.isPending ||
    updateProfile.isPending ||
    addSample.isPending ||
    uploadAvatar.isPending ||
    useLibrarySample.isPending;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>
            {editingProfileId
              ? t('profileForm.title.edit')
              : t('profileForm.title.create')}
          </DialogTitle>
          <DialogDescription>{t('profileForm.description')}</DialogDescription>
        </DialogHeader>

        <div className="overflow-y-auto pr-2">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
                <div className="space-y-4">
                  {editingProfileId ? (
                    <SampleList profileId={editingProfileId} />
                  ) : (
                    <>
                      <Tabs
                        value={sampleMode}
                        onValueChange={(value) => {
                          if (isRecording && value !== 'record') cancelRecording();
                          setSampleMode(value as 'upload' | 'record' | 'library');
                        }}
                      >
                        <TabsList className="grid w-full grid-cols-3">
                          <TabsTrigger value="upload" className="flex items-center gap-2">
                            <Upload className="h-4 w-4 shrink-0" />
                            {t('profileForm.sampleTabs.upload')}
                          </TabsTrigger>
                          <TabsTrigger value="record" className="flex items-center gap-2">
                            <Mic className="h-4 w-4 shrink-0" />
                            {t('profileForm.sampleTabs.record')}
                          </TabsTrigger>
                          <TabsTrigger value="library" className="flex items-center gap-2">
                            <Library className="h-4 w-4 shrink-0" />
                            {t('profileForm.sampleTabs.library', { defaultValue: 'Library' })}
                          </TabsTrigger>
                        </TabsList>

                        <TabsContent value="upload" className="space-y-4">
                          <FormField
                            control={form.control}
                            name="sampleFile"
                            render={({ field: { onChange, name } }) => (
                              <AudioSampleUpload
                                file={selectedFile}
                                onFileChange={onChange}
                                onPlayPause={handlePlayPause}
                                isPlaying={isPlaying}
                                isValidating={isValidatingAudio}
                                fieldName={name}
                              />
                            )}
                          />
                        </TabsContent>

                        <TabsContent value="record" className="space-y-4">
                          <FormField
                            control={form.control}
                            name="sampleFile"
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

                        <TabsContent value="library" className="space-y-4">
                          <p className="text-sm text-muted-foreground">
                            Create the profile first, then add library samples from the profile.
                          </p>
                        </TabsContent>
                      </Tabs>

                      <FormField
                        control={form.control}
                        name="referenceText"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>{t('profileForm.fields.referenceText')}</FormLabel>
                            <FormControl>
                              <Textarea
                                placeholder={t('profileForm.fields.referenceTextPlaceholder')}
                                className="min-h-[100px]"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </>
                  )}

                  {editingProfileId && (
                    <div className="space-y-3">
                      <FormLabel>
                        {t('profileForm.sampleTabs.library', { defaultValue: 'Audio library' })}
                      </FormLabel>
                      <FormField
                        control={form.control}
                        name="referenceText"
                        render={({ field }) => (
                          <FormItem>
                            <FormControl>
                              <Textarea
                                placeholder={t('profileForm.fields.referenceTextPlaceholder')}
                                className="min-h-[80px]"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <AudioLibraryBrowser onSelect={(item) => handleLibrarySelect(item.id)} />
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <FormField
                    control={form.control}
                    name="avatarFile"
                    render={() => (
                      <FormItem>
                        <FormControl>
                          <div className="flex justify-center pt-2 pb-2">
                            <div className="relative group">
                              <div className="h-24 w-24 rounded-full bg-muted flex items-center justify-center shrink-0 overflow-hidden border-2 border-border">
                                {avatarPreview ? (
                                  <img
                                    src={avatarPreview}
                                    alt={t('profileForm.avatar.alt')}
                                    className="h-full w-full object-cover"
                                  />
                                ) : (
                                  <Mic className="h-10 w-10 text-muted-foreground" />
                                )}
                              </div>
                              <button
                                type="button"
                                onClick={() => avatarInputRef.current?.click()}
                                className="absolute inset-0 rounded-full bg-accent/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer"
                              >
                                <Edit2 className="h-6 w-6 text-accent-foreground" />
                              </button>
                              {(avatarPreview || editingProfile?.avatar_path) && (
                                <button
                                  type="button"
                                  onClick={handleRemoveAvatar}
                                  disabled={deleteAvatar.isPending}
                                  className="absolute bottom-0 right-0 h-6 w-6 rounded-full bg-background/60 backdrop-blur-sm text-muted-foreground flex items-center justify-center hover:bg-background/80 hover:text-foreground transition-colors shadow-sm border border-border/50"
                                >
                                  <X className="h-3.5 w-3.5" />
                                </button>
                              )}
                            </div>
                            <input
                              ref={avatarInputRef}
                              type="file"
                              accept="image/png,image/jpeg,image/webp"
                              onChange={handleAvatarFileChange}
                              className="hidden"
                            />
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{t('profileForm.fields.name')}</FormLabel>
                        <FormControl>
                          <Input placeholder={t('profileForm.fields.namePlaceholder')} {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{t('profileForm.fields.descriptionLabel')}</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder={t('profileForm.fields.descriptionPlaceholder')}
                            {...field}
                          />
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
                        <FormLabel>{t('profileForm.fields.language')}</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {LANGUAGE_OPTIONS.map((lang) => (
                              <SelectItem key={lang.value} value={lang.value}>
                                {lang.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {editingProfileId && (
                    <div className="space-y-2">
                      <FormLabel>{t('profileForm.fields.defaultEffects')}</FormLabel>
                      <EffectsChainEditor
                        value={profileEffectsChain}
                        onChange={(chain) => {
                          setProfileEffectsChain(chain);
                          setEffectsDirty(true);
                        }}
                        compact
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-2 justify-between pt-4 border-t">
                <div>
                  {editingProfileId && (
                    <Button
                      type="button"
                      variant="destructive"
                      onClick={handleDelete}
                      disabled={deleteProfile.isPending}
                    >
                      {t('profileForm.actions.delete', { defaultValue: 'Delete' })}
                    </Button>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
                    {t('common.cancel')}
                  </Button>
                  <Button type="submit" disabled={savePending}>
                    {savePending
                      ? t('profileForm.actions.saving')
                      : editingProfileId
                        ? t('profileForm.actions.saveChanges')
                        : t('profileForm.actions.createProfile')}
                  </Button>
                </div>
              </div>
            </form>
          </Form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
