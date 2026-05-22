const variant = process.env.EXPO_PUBLIC_APP_VARIANT ?? 'client';

const configs = {
  client: {
    appName: 'Annai Illam',
    storagePrefix: 'client',
  },
  worker: {
    appName: 'Annai Illam Worker',
    storagePrefix: 'worker',
  },
} as const;

export const appVariantConfig = configs[variant as keyof typeof configs] ?? configs.client;
