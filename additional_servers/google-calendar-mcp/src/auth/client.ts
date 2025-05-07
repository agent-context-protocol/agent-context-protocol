import { OAuth2Client } from 'google-auth-library';
import * as fs from 'fs/promises';
import { getKeysFilePath } from './utils.js';

export async function initializeOAuth2Client(): Promise<OAuth2Client> {
  try {
    const keysContent = await fs.readFile(getKeysFilePath(), "utf-8");
    const keys = JSON.parse(keysContent);

    const { client_id, client_secret, redirect_uris } = keys.installed;

    // Use the first redirect URI as the default for the base client
    return new OAuth2Client({
      clientId: client_id,
      clientSecret: client_secret,
      redirectUri: redirect_uris[0], 
    });
  } catch (error) {
    throw new Error(`Error loading OAuth keys: ${error instanceof Error ? error.message : error}`);
  }
}

export async function loadCredentials(): Promise<{ client_id: string; client_secret: string }> {
  try {
    const keysContent = await fs.readFile(getKeysFilePath(), "utf-8");
    const keys = JSON.parse(keysContent);
    const { client_id, client_secret } = keys.installed;
    if (!client_id || !client_secret) {
        throw new Error('Client ID or Client Secret missing in keys file.');
    }
    return { client_id, client_secret };
  } catch (error) {
    throw new Error(`Error loading credentials: ${error instanceof Error ? error.message : error}`);
  }
} 