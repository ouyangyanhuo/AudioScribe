import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  redirect,
} from '@tanstack/react-router';
import { AppFrame } from '@/components/AppFrame/AppFrame';
import { EffectsTab } from '@/components/EffectsTab/EffectsTab';
import { MainEditor } from '@/components/MainEditor/MainEditor';
import { AboutPage } from '@/components/ServerTab/AboutPage';
import { ChangelogPage } from '@/components/ServerTab/ChangelogPage';
import { GeneralPage } from '@/components/ServerTab/GeneralPage';
import { GenerationPage } from '@/components/ServerTab/GenerationPage';
import { LogsPage } from '@/components/ServerTab/LogsPage';
import { SettingsLayout } from '@/components/ServerTab/ServerTab';
import { Sidebar } from '@/components/Sidebar';
import { StoriesTab } from '@/components/StoriesTab/StoriesTab';
import { Toaster } from '@/components/ui/toaster';
import { VoicesTab } from '@/components/VoicesTab/VoicesTab';
import { useGenerationProgress } from '@/lib/hooks/useGenerationProgress';
import { useModelDownloadToast } from '@/lib/hooks/useModelDownloadToast';
import { MODEL_DISPLAY_NAMES, useRestoreActiveTasks } from '@/lib/hooks/useRestoreActiveTasks';

const isMacOS = () => navigator.platform.toLowerCase().includes('mac');

function RootLayout() {
  const activeDownloads = useRestoreActiveTasks();
  useGenerationProgress();

  return (
    <AppFrame>
      <div className="flex flex-1 min-h-0 overflow-hidden">
        <Sidebar isMacOS={isMacOS()} />
        <main className="flex-1 ml-20 overflow-hidden flex flex-col">
          <div className="container mx-auto px-8 max-w-[1800px] h-full overflow-hidden flex flex-col">
            <Outlet />
          </div>
        </main>
      </div>

      {activeDownloads.map((download) => (
        <DownloadToastRestorer
          key={download.model_name}
          modelName={download.model_name}
          displayName={MODEL_DISPLAY_NAMES[download.model_name] || download.model_name}
        />
      ))}

      <Toaster />
    </AppFrame>
  );
}

function DownloadToastRestorer({
  modelName,
  displayName,
}: {
  modelName: string;
  displayName: string;
}) {
  useModelDownloadToast({ modelName, displayName, enabled: true });
  return null;
}

const rootRoute = createRootRoute({ component: RootLayout });
const indexRoute = createRoute({ getParentRoute: () => rootRoute, path: '/', component: MainEditor });
const storiesRoute = createRoute({ getParentRoute: () => rootRoute, path: '/stories', component: StoriesTab });
const voicesRoute = createRoute({ getParentRoute: () => rootRoute, path: '/voices', component: VoicesTab });
const effectsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/effects', component: EffectsTab });
const settingsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/settings', component: SettingsLayout });
const settingsGeneralRoute = createRoute({ getParentRoute: () => settingsRoute, path: '/', component: GeneralPage });
const settingsGenerationRoute = createRoute({ getParentRoute: () => settingsRoute, path: '/generation', component: GenerationPage });
const settingsLogsRoute = createRoute({ getParentRoute: () => settingsRoute, path: '/logs', component: LogsPage });
const settingsChangelogRoute = createRoute({ getParentRoute: () => settingsRoute, path: '/changelog', component: ChangelogPage });
const settingsAboutRoute = createRoute({ getParentRoute: () => settingsRoute, path: '/about', component: AboutPage });
const serverRedirectRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/server',
  beforeLoad: () => {
    throw redirect({ to: '/settings' });
  },
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  storiesRoute,
  voicesRoute,
  effectsRoute,
  settingsRoute.addChildren([
    settingsGeneralRoute,
    settingsGenerationRoute,
    settingsLogsRoute,
    settingsChangelogRoute,
    settingsAboutRoute,
  ]),
  serverRedirectRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
