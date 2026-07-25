# Fix Generate Profile Assets pipeline — approccio 2 (curl-based trophy)

## Context

La pipeline `Generate Profile Assets` fallisce al passo "Generate trophy" con:
```
Error fetching user info for username: Crovax1990
Failed to fetch user info. Check token, username and rate limits.
```

**Root cause:** L'action `Erik-Donath/github-profile-trophy@feature/generate-svg` è stata aggiornata 19 ore fa con modifiche alle GraphQL API call. Il workflow ha `permissions: contents: write` ma non `metadata: read` → il `GITHUB_TOKEN` non può autenticare le chiamate API. Il servizio principale `github-profile-trophy.vercel.app` è stato paywallato (HTTP 402).

**Approccio scelto:** Rimpiazzare l'action con `curl` verso endpoint Vercel funzionanti, stesso pattern già usato per stats card e streak.

## Endpoint verificati funzionanti

| Mirror | Stato |
|--------|-------|
| `github-profile-trophy-orcin-eta.vercel.app` | ✅ 200 SVG |
| `github-profile-trophy-unserori.vercel.app` | ✅ 200 SVG |
| `trophy.benkou.dev` | ✅ 200 SVG |
| `github-profile-trophy.vercel.app` (main) | ❌ 402 paywall |
| Altri mirror | ❌ 404 |

## Modifiche

### File: `.github/workflows/snake.yml`

1. **Rimuovere** lo step `Erik-Donath/github-profile-trophy@feature/generate-svg`
2. **Aggiungere** `mkdir -p dist` (prerequisito per i curl)
3. **Aggiungere** step `curl` primario verso `orcin-eta`
4. **Aggiungere** step `curl` fallback verso `unserori` (con `if: failure()`)

Non si tocca altro (stats, streak, snake, push a output branch).

### Vantaggi

- Uniforma tutto il workflow allo stesso pattern (curl → SVG locale)
- Zero dipendenze da `GITHUB_TOKEN` per le API call
- Fallback automatico se il mirror primario va giù
- Nessuna azione di terze parti che può rompersi con aggiornamenti

## Verifica

1. Pushare la modifica
2. Triggerare manualmente `Generate Profile Assets` da Actions
3. Verificare che tutti i passi vadano a buon fine
4. Controllare che le immagini sul profilo GitHub compaiano correttamente
