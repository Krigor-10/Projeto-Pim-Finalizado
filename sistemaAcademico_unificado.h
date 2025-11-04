#ifndef SISTEMAACADEMICO_H_INCLUDED
#define SISTEMAACADEMICO_H_INCLUDED

/*
 * sistemaacademico.h - Versao unificada e corrigida.
 *
 * Contem:
 * - Estrutura UsuarioCSV e funcoes utilitarias.
 * - Funcoes de manipulacao de arquivo (CSV plano).
 * - Funcoes CRUD (Create, Read, Update, Delete) de usuarios.
 * - Menus de interacao para diferentes niveis de acesso.
 */

#define _CRT_SECURE_NO_WARNINGS

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>
#include <locale.h>

#ifdef _WIN32
    #include <windows.h>
    #include <direct.h>
    #include <conio.h>
    #define MKDIR(p) _mkdir(p)
    #define PATH_SEP "\\"
    #define STRCASECMP _stricmp
#else
    #include <unistd.h>
    #include <sys/stat.h>
    #include <strings.h> /* strcasecmp */
    #define MKDIR(p) mkdir((p), 0700)
    #define PATH_SEP "/"
    #define STRCASECMP strcasecmp
#endif

#define ARQ_SISTEMA "sistemaAcademico.csv"
#define DIR_BACKUPS "backups"
#define MAX_LINE 2048

/* ----------------- ESTRUTURA USUARIO ----------------- */
typedef struct {
    int id;
    char nome[256];
    char email[256];
    char senha[128];
    char nivel[64];
    char curso[128];
    char turma[64];
    int idade;
    float np1, np2, pim, media;
    char atividade[32];
} UsuarioCSV;

/* ----------------- DECLARACOES DE FUNCOES ----------------- */
void initSistema(void);
void trim(char *s);
int validarEmail(const char *email);
void lerSenhaOculta(char *senha, size_t maxLen);
int arquivoExiste(const char *nome);
void garantirPasta(const char *pasta);
int backupSistema(void);
void criarArquivoSistemaSeNaoExiste(void);
int parseLinhaUsuario(const char *line, UsuarioCSV *u);
void formatarLinhaUsuario(const UsuarioCSV *u, char *out, size_t outsz);
int verificarLoginUnico(const char *email, const char *senha, UsuarioCSV *out);
int obterUltimoIDUsuarios(void);
int emailDuplicado(const char *email);
int adicionarUsuario(const UsuarioCSV *u_in);
int listarTodosUsuarios(void);
int alterarUsuarioPorID(int idBusca, const UsuarioCSV *novo);
int excluirUsuarioPorID(int idBusca);
void menuAlunoUnificado(const UsuarioCSV *u);
void menuProfessorUnificado(const UsuarioCSV *u);
void menuCoordenadorUnificado(const UsuarioCSV *u);
void menuAdministradorUnificado(const UsuarioCSV *u);
void executarSistema(void);


/* ----------------- DEFINICOES DE FUNCOES ----------------- */

void initSistema(void) {
    setlocale(LC_ALL, "");
#ifdef _WIN32
    /* tenta forcar UTF-8 no console Windows */
    SetConsoleOutputCP(65001); // CP_UTF8 = 65001
    SetConsoleCP(65001);       // CP_UTF8 = 65001
    /* Nota: 'SetConsoleOutputCP' nao funciona perfeitamente em versoes antigas do Windows. */
#endif
}

void trim(char *s) {
    if (!s) return;
    char *p = s;
    while (*p && isspace((unsigned char)*p)) p++;
    if (p != s) memmove(s, p, strlen(p) + 1);
    size_t L = strlen(s);
    while (L > 0 && isspace((unsigned char)s[L - 1])) s[--L] = '\0';
}

int validarEmail(const char *email) {
    if (!email) return 0;
    const char *at = strchr(email, '@');
    if (!at || at == email) return 0;
    const char *dot = strchr(at + 1, '.');
    if (!dot || dot == at + 1) return 0;
    if (*(dot + 1) == '\0') return 0;
    return 1;
}

void lerSenhaOculta(char *senha, size_t maxLen) {
    if (!senha || maxLen == 0) return;
#ifdef _WIN32
    size_t idx = 0; int ch;
    while ((ch = _getch()) != '\r' && ch != '\n' && idx + 1 < maxLen) {
        if (ch == '\b') {
            if (idx > 0) { idx--; printf("\b \b"); }
        } else {
            senha[idx++] = (char)ch;
            printf("*");
        }
    }
    senha[idx] = '\0';
    printf("\n");
#else
    /* No Linux/macOS, o terminal deve estar configurado para modo cbreak/raw,
       o que 'conio.h' (simulada) faria. Usaremos fgets para simplicidade */
    if (fgets(senha, (int)maxLen, stdin)) {
        senha[strcspn(senha, "\n")] = '\0';
    } else senha[0] = '\0';
#endif
}

int arquivoExiste(const char *nome) {
    if (!nome) return 0;
    FILE *f = fopen(nome, "r");
    if (f) { fclose(f); return 1; }
    return 0;
}

void garantirPasta(const char *pasta) {
    if (!pasta) return;
    /* Usar 0700 no Windows nao e necessario, mas mantemos o padrao Linux */
    if (!arquivoExiste(pasta)) MKDIR(pasta);
}

void now_str(char *dest, size_t n) {
    time_t t = time(NULL);
    struct tm tm;
#ifdef _WIN32
    struct tm *tptr = localtime(&t);
    if (tptr) tm = *tptr;
    else memset(&tm,0,sizeof(tm));
#else
    localtime_r(&t, &tm);
#endif
    strftime(dest, n, "%Y%m%d_%H%M%S", &tm);
}

/* ----------------- BACKUP ----------------- */

int backupSistema(void) {
    if (!arquivoExiste(ARQ_SISTEMA)) return 0;
    garantirPasta(DIR_BACKUPS);
    char stamp[64]; now_str(stamp, sizeof(stamp));
    char dest[512];
    snprintf(dest, sizeof(dest), "%s%ssistemaAcademico_backup_%s.csv", DIR_BACKUPS, PATH_SEP, stamp);
    FILE *fs = fopen(ARQ_SISTEMA, "rb");
    if (!fs) return 0;
    FILE *fd = fopen(dest, "wb");
    if (!fd) { fclose(fs); return 0; }
    char buf[4096]; size_t r;
    while ((r = fread(buf,1,sizeof(buf),fs))>0) fwrite(buf,1,r,fd);
    fclose(fs); fclose(fd);
    printf("Backup criado com sucesso: %s\n", dest);
    return 1;
}

/* ----------------- ARQUIVO INICIAL ----------------- */

void criarArquivoSistemaSeNaoExiste(void) {
    if (arquivoExiste(ARQ_SISTEMA)) return;
    FILE *f = fopen(ARQ_SISTEMA, "w");
    if (!f) {
        printf("Erro ao criar arquivo do sistema!\n");
        return;
    }
    /* Cabecalho: id;nome;email;senha;nivel;curso;turma;idade;np1;np2;pim;media;atividade */
    fprintf(f, "id;nome;email;senha;nivel;curso;turma;idade;np1;np2;pim;media;atividade\n");
    /* Usuario admin padrao */
    fprintf(f, "1;Administrador;admin@admin.com;admin;Administrador;Sistema;Geral;30;0;0;0;0;Ativo\n");
    fclose(f);
    printf("Arquivo do sistema criado com usuario padrao: admin@admin.com / senha: admin\n");
}

/* ----------------- PARSE / FORMATACAO ----------------- */

int parseLinhaUsuario(const char *line, UsuarioCSV *u) {
    if (!line || !u) return 0;
    /* Faz uma copia para que strtok possa modificar */
    char *buf = strdup(line);
    if (!buf) return 0;

    trim(buf);
    if (buf[0] == '\0') { free(buf); return 0; }
    /* ignorar header se passado por acidente */
    if (STRCASECMP(buf, "id;nome;email;senha;nivel;curso;turma;idade;np1;np2;pim;media;atividade\n") == 0) { free(buf); return 0; }

    /* Usando strtok */
    char *tok = strtok(buf, ";");
    if (!tok) { free(buf); return 0; }
    u->id = atoi(tok);

    tok = strtok(NULL, ";"); if (!tok) { free(buf); return 0; } strncpy(u->nome, tok, sizeof(u->nome)-1); u->nome[sizeof(u->nome)-1]=0;
    tok = strtok(NULL, ";"); if (!tok) { free(buf); return 0; } strncpy(u->email, tok, sizeof(u->email)-1); u->email[sizeof(u->email)-1]=0;
    tok = strtok(NULL, ";"); if (!tok) { free(buf); return 0; } strncpy(u->senha, tok, sizeof(u->senha)-1); u->senha[sizeof(u->senha)-1]=0;
    tok = strtok(NULL, ";"); if (!tok) { free(buf); return 0; } strncpy(u->nivel, tok, sizeof(u->nivel)-1); u->nivel[sizeof(u->nivel)-1]=0;
    tok = strtok(NULL, ";"); if (!tok) { free(buf); return 0; } strncpy(u->curso, tok, sizeof(u->curso)-1); u->curso[sizeof(u->curso)-1]=0;
    tok = strtok(NULL, ";"); if (!tok) { free(buf); return 0; } strncpy(u->turma, tok, sizeof(u->turma)-1); u->turma[sizeof(u->turma)-1]=0;
    tok = strtok(NULL, ";"); if (!tok) tok = "0"; u->idade = atoi(tok);

    tok = strtok(NULL, ";"); if (!tok) tok = "0"; u->np1 = (float)atof(tok);
    tok = strtok(NULL, ";"); if (!tok) tok = "0"; u->np2 = (float)atof(tok);
    tok = strtok(NULL, ";"); if (!tok) tok = "0"; u->pim = (float)atof(tok);
    tok = strtok(NULL, ";"); if (!tok) tok = "0"; u->media = (float)atof(tok);
    tok = strtok(NULL, ";"); if (!tok) tok = "Ativo"; strncpy(u->atividade, tok, sizeof(u->atividade)-1); u->atividade[sizeof(u->atividade)-1]=0;

    trim(u->nome); trim(u->email); trim(u->senha); trim(u->nivel);
    trim(u->curso); trim(u->turma); trim(u->atividade);

    free(buf);
    return 1;
}

void formatarLinhaUsuario(const UsuarioCSV *u, char *out, size_t outsz) {
    if (!u || !out) return;
    snprintf(out, outsz, "%d;%s;%s;%s;%s;%s;%s;%d;%.2f;%.2f;%.2f;%.2f;%s\n",
             u->id,
             u->nome,
             u->email,
             u->senha,
             u->nivel,
             u->curso,
             u->turma,
             u->idade,
             u->np1, u->np2, u->pim, u->media,
             u->atividade[0] ? u->atividade : "Ativo");
}

/* ----------------- OPERACOES SOBRE ARQUIVO (CSV PLANO) ----------------- */

int verificarLoginUnico(const char *email, const char *senha, UsuarioCSV *out) {
    if (!email || !senha || !arquivoExiste(ARQ_SISTEMA)) return 0;
    FILE *f = fopen(ARQ_SISTEMA, "r");
    if (!f) return 0;
    char linha[MAX_LINE];
    /* pula cabecalho */
    if (!fgets(linha, sizeof(linha), f)) { fclose(f); return 0; }
    while (fgets(linha, sizeof(linha), f)) {
        char tmp[MAX_LINE]; strncpy(tmp, linha, sizeof(tmp)-1); tmp[sizeof(tmp)-1]=0;
        trim(tmp);
        UsuarioCSV u; memset(out,0,sizeof(UsuarioCSV));
        if (!parseLinhaUsuario(tmp, out)) continue; /* parseLinhaUsuario ja usa strtok(tmp) */
        if (STRCASECMP(out->email, email) == 0 && strcmp(out->senha, senha) == 0) {
            fclose(f);
            return 1;
        }
    }
    fclose(f);
    return 0;
}

int obterUltimoIDUsuarios(void) {
    if (!arquivoExiste(ARQ_SISTEMA)) return 0;
    FILE *f = fopen(ARQ_SISTEMA, "r");
    if (!f) return 0;
    char linha[MAX_LINE];
    int maxID = 0;
    /* pula cabecalho */
    if (!fgets(linha, sizeof(linha), f)) { fclose(f); return 0; }
    while (fgets(linha, sizeof(linha), f)) {
        char tmp[MAX_LINE]; strncpy(tmp, linha, sizeof(tmp)-1); tmp[sizeof(tmp)-1]=0;
        trim(tmp);
        UsuarioCSV u; memset(&u,0,sizeof(u));
        /* Nao podemos usar parseLinhaUsuario aqui pois ela usa strtok, que e global.
           E melhor reescrever a logica de ID simples, ou garantir o parse completo.
           Usaremos a logica de ID simples abaixo para evitar conflitos de strtok global. */
        char *p = tmp;
        while (*p && isspace((unsigned char)*p)) p++;
        if (!isdigit((unsigned char)*p)) continue;

        int id = atoi(p);
        if (id > maxID) maxID = id;
    }
    fclose(f);
    return maxID;
}

int emailDuplicado(const char *email) {
    if (!email || !arquivoExiste(ARQ_SISTEMA)) return 0;
    FILE *f = fopen(ARQ_SISTEMA, "r");
    if (!f) return 0;
    char linha[MAX_LINE];
    /* pula cabecalho */
    if (!fgets(linha, sizeof(linha), f)) { fclose(f); return 0; }
    while (fgets(linha, sizeof(linha), f)) {
        char tmp[MAX_LINE]; strncpy(tmp, linha, sizeof(tmp)-1); tmp[sizeof(tmp)-1]=0;
        trim(tmp);
        UsuarioCSV u; memset(&u,0,sizeof(u));
        if (!parseLinhaUsuario(tmp, &u)) continue;
        if (STRCASECMP(u.email, email) == 0) { fclose(f); return 1; }
    }
    fclose(f);
    return 0;
}

/* ----------------- CRUD ----------------- */

int adicionarUsuario(const UsuarioCSV *u_in) {
    if (!u_in) return 0;
    if (strlen(u_in->nome) == 0 || strlen(u_in->email) == 0 || strlen(u_in->senha) == 0 || strlen(u_in->nivel) == 0) {
        printf("Campos obrigatorios vazios.\n"); return 0;
    }
    if (!validarEmail(u_in->email)) { printf("Email invalido.\n"); return 0; }
    if (emailDuplicado(u_in->email)) { printf("Email ja cadastrado.\n"); return 0; }

    int novoID = obterUltimoIDUsuarios() + 1;
    UsuarioCSV u = *u_in;
    u.id = novoID;
    if (!u.atividade[0]) strncpy(u.atividade, "Ativo", sizeof(u.atividade)-1); u.atividade[sizeof(u.atividade)-1]=0;

    char linha[MAX_LINE];
    formatarLinhaUsuario(&u, linha, sizeof(linha));

    /* fazer backup antes de alterar */
    backupSistema();

    FILE *f = fopen(ARQ_SISTEMA, "a");
    if (!f) { printf("Erro ao abrir arquivo para adicionar.\n"); return 0; }
    fputs(linha, f);
    fclose(f);
    printf("Usuario adicionado com ID %d\n", novoID);
    return 1;
}

int listarTodosUsuarios(void) {
    if (!arquivoExiste(ARQ_SISTEMA)) { printf("Nenhum usuario cadastrado.\n"); return 0; }
    FILE *f = fopen(ARQ_SISTEMA, "r");
    if (!f) { printf("Erro ao abrir arquivo.\n"); return 0; }
    char linha[MAX_LINE];
    /* cabecalho */
    if (!fgets(linha, sizeof(linha), f)) { fclose(f); printf("Arquivo vazio.\n"); return 0; }
    printf("\n==================================== LISTAGEM DE USUARIOS ====================================\n");
    printf("%-5s | %-30s | %-30s | %-15s | %-10s | %-5s\n", "ID", "Nome", "Email", "Nivel", "Turma", "Atv.");
    printf("------------------------------------------------------------------------------------------------\n");
    while (fgets(linha, sizeof(linha), f)) {
        char tmp[MAX_LINE]; strncpy(tmp, linha, sizeof(tmp)-1); tmp[sizeof(tmp)-1]=0;
        trim(tmp);
        UsuarioCSV u; memset(&u,0,sizeof(u));
        if (!parseLinhaUsuario(tmp, &u)) continue;
        printf("%-5d | %-30.30s | %-30.30s | %-15.15s | %-10.10s | %-5.5s\n",
               u.id, u.nome, u.email, u.nivel, u.turma, u.atividade);
    }
    fclose(f);
    return 1;
}

int alterarUsuarioPorID(int idBusca, const UsuarioCSV *novo) {
    if (!arquivoExiste(ARQ_SISTEMA) || !novo) return 0;
    FILE *f = fopen(ARQ_SISTEMA, "r");
    if (!f) return 0;
    /* ler todo o arquivo para memoria (simples) */
    char **linhas = NULL;
    size_t count = 0;
    char linha[MAX_LINE];
    while (fgets(linha, sizeof(linha), f)) {
        char *c = strdup(linha);
        if (!c) { fclose(f); /* liberar linhas */ for (size_t i=0;i<count;i++) free(linhas[i]); free(linhas); return 0; }
        char **tmp = realloc(linhas, sizeof(char*)*(count+1));
        if (!tmp) { free(c); fclose(f); for (size_t i=0;i<count;i++) free(linhas[i]); free(linhas); return 0; }
        linhas = tmp; linhas[count++] = c;
    }
    fclose(f);

    int found = 0;
    /* primeiro elemento é o cabecalho (mantemos) */
    for (size_t i = 0; i < count; i++) {
        char copy[MAX_LINE]; strncpy(copy, linhas[i], sizeof(copy)-1); copy[sizeof(copy)-1]=0;
        trim(copy);
        if (i == 0 && (STRCASECMP(copy, "id;nome;email;senha;nivel;curso;turma;idade;np1;np2;pim;media;atividade") == 0)) continue;
        UsuarioCSV u; memset(&u,0,sizeof(u));
        if (!parseLinhaUsuario(copy, &u)) continue;
        if (u.id == idBusca) {
            /* substituir linha */
            char nova[MAX_LINE];
            UsuarioCSV temp = *novo;
            temp.id = idBusca;
            if (!temp.atividade[0]) strncpy(temp.atividade, "Ativo", sizeof(temp.atividade)-1); temp.atividade[sizeof(temp.atividade)-1]=0;
            formatarLinhaUsuario(&temp, nova, sizeof(nova));
            free(linhas[i]);
            linhas[i] = strdup(nova);
            found = 1;
            break;
        }
    }

    if (!found) {
        for (size_t i=0;i<count;i++) free(linhas[i]); free(linhas);
        printf("Usuario ID %d nao encontrado.\n", idBusca);
        return 0;
    }

    /* backup e sobrescrever arquivo */
    backupSistema();
    FILE *fw = fopen(ARQ_SISTEMA, "w");
    if (!fw) { for (size_t i=0;i<count;i++) free(linhas[i]); free(linhas); return 0; }
    for (size_t i=0;i<count;i++) {
        fputs(linhas[i], fw);
        free(linhas[i]);
    }
    free(linhas);
    fclose(fw);
    printf("Usuario ID %d alterado com sucesso.\n", idBusca);
    return 1;
}

int excluirUsuarioPorID(int idBusca) {
    if (!arquivoExiste(ARQ_SISTEMA)) return 0;
    FILE *f = fopen(ARQ_SISTEMA, "r");
    if (!f) return 0;
    char **linhas = NULL;
    size_t count = 0;
    char linha[MAX_LINE];
    while (fgets(linha, sizeof(linha), f)) {
        char *c = strdup(linha);
        if (!c) { fclose(f); for (size_t i=0;i<count;i++) free(linhas[i]); free(linhas); return 0; }
        char **tmp = realloc(linhas, sizeof(char*)*(count+1));
        if (!tmp) { free(c); fclose(f); for (size_t i=0;i<count;i++) free(linhas[i]); free(linhas); return 0; }
        linhas = tmp; linhas[count++] = c;
    }
    fclose(f);

    int removed = 0;
    /* reconstruir sem a linha removida */
    FILE *fw = fopen("tmp_sistema.csv", "w");
    if (!fw) { for (size_t i=0;i<count;i++) free(linhas[i]); free(linhas); return 0; }

    for (size_t i=0;i<count;i++) {
        char copy[MAX_LINE]; strncpy(copy, linhas[i], sizeof(copy)-1); copy[sizeof(copy)-1]=0;
        trim(copy);
        if (i == 0 && (STRCASECMP(copy, "id;nome;email;senha;nivel;curso;turma;idade;np1;np2;pim;media;atividade") == 0)) {
            fputs(linhas[i], fw); continue;
        }
        UsuarioCSV u; memset(&u,0,sizeof(u));
        if (!parseLinhaUsuario(copy, &u)) { fputs(linhas[i], fw); continue; }
        if (u.id == idBusca) { removed = 1; /* pula */ }
        else fputs(linhas[i], fw);
    }
    for (size_t i=0;i<count;i++) free(linhas[i]);
    free(linhas);
    fclose(fw);

    if (!removed) {
        remove("tmp_sistema.csv");
        printf("Usuario ID %d nao encontrado.\n", idBusca);
        return 0;
    }

    /* backup e renomear tmp para original */
    backupSistema();
#ifdef _WIN32
    remove(ARQ_SISTEMA);
    rename("tmp_sistema.csv", ARQ_SISTEMA);
#else
    if (rename("tmp_sistema.csv", ARQ_SISTEMA) != 0) {
        printf("Erro ao substituir arquivo.\n"); remove("tmp_sistema.csv"); return 0;
    }
#endif
    printf("Usuario ID %d excluido com sucesso.\n", idBusca);
    return 1;
}

/* ----------------- MENUS ----------------- */

void mostrarUsuario(const UsuarioCSV *u) {
    if (!u) return;
    printf("\nID: %d\nNome: %s\nEmail: %s\nIdade: %d\nNivel: %s\nCurso: %s\nTurma: %s\nAtividade: %s\nNotas: NP1=%.2f NP2=%.2f PIM=%.2f Media=%.2f\n",
           u->id, u->nome, u->email, u->idade, u->nivel, u->curso, u->turma, u->atividade,
           u->np1, u->np2, u->pim, u->media);
}

void menuAlunoUnificado(const UsuarioCSV *u) {
    int opc;
    do {
        printf("\n=== MENU ALUNO: %s ===\n", u->nome);
        printf("1 - Meus dados\n2 - Ver turma\n3 - Ver notas\n0 - Sair\n> ");
        if (scanf("%d", &opc)!=1) { while(getchar()!='\n'); opc=-1; }
        while(getchar()!='\n');
        switch (opc) {
            case 1: mostrarUsuario(u); break;
            case 2: printf("Turma: %s\n", u->turma); break;
            case 3: printf("Notas: NP1=%.2f NP2=%.2f PIM=%.2f Media=%.2f\n", u->np1, u->np2, u->pim, u->media); break;
            case 0: break;
            default: printf("Opcao invalida.\n");
        }
    } while (opc != 0);
}

void menuProfessorUnificado(const UsuarioCSV *u) {
    int opc;
    do {
        printf("\n=== MENU PROFESSOR: %s ===\n", u->nome);
        printf("1 - Meus dados\n2 - Lancar notas (nao implementado na demo)\n0 - Sair\n> ");
        if (scanf("%d", &opc)!=1) { while(getchar()!='\n'); opc=-1; }
        while(getchar()!='\n');
        if (opc == 1) mostrarUsuario(u);
        else if (opc == 2) printf("Funcao de lancar notas (precisa implementar).\n");
        else if (opc != 0) printf("Opcao invalida.\n");
    } while (opc != 0);
}

void menuCoordenadorUnificado(const UsuarioCSV *u) {
    int opc;
    do {
        printf("\n=== MENU COORDENADOR: %s ===\n", u->nome);
        printf("1 - Meus dados\n2 - Gerenciar turmas (nao implementado)\n3 - Gerenciar notas (nao implementado)\n0 - Sair\n> ");
        if (scanf("%d", &opc)!=1) { while(getchar()!='\n'); opc=-1; }
        while(getchar()!='\n');
        if (opc == 1) mostrarUsuario(u);
        else if (opc == 2) printf("Funcao gerenciar turmas (precisa implementar).\n");
        else if (opc == 3) printf("Funcao gerenciar notas (precisa implementar).\n");
        else if (opc != 0) printf("Opcao invalida.\n");
    } while (opc != 0);
}

/* Funcoes administrativas: menu com CRUD integrado */
void gerenciarUsuariosUI(void) {
    int opc = -1;
    while (1) {
        printf("\n--- GERENCIAR USUARIOS ---\n");
        printf("1 - Listar todos\n2 - Adicionar\n3 - Alterar por ID\n4 - Excluir por ID\n0 - Voltar\n> ");
        if (scanf("%d", &opc)!=1) { while(getchar()!='\n'); opc=-1; }
        while(getchar()!='\n');
        if (opc == 1) {
            listarTodosUsuarios();
        } else if (opc == 2) {
            UsuarioCSV u; memset(&u,0,sizeof(u));
            printf("Nome: "); fgets(u.nome, sizeof(u.nome), stdin); u.nome[strcspn(u.nome, "\n")] = 0; trim(u.nome);
            printf("Email: "); fgets(u.email, sizeof(u.email), stdin); u.email[strcspn(u.email, "\n")] = 0; trim(u.email);
            printf("Senha: "); lerSenhaOculta(u.senha, sizeof(u.senha)); trim(u.senha);
            printf("Nivel (Administrador/Coordenador/Professor/Aluno): "); fgets(u.nivel, sizeof(u.nivel), stdin); u.nivel[strcspn(u.nivel, "\n")] = 0; trim(u.nivel);
            printf("Curso: "); fgets(u.curso, sizeof(u.curso), stdin); u.curso[strcspn(u.curso, "\n")] = 0; trim(u.curso);
            printf("Turma: "); fgets(u.turma, sizeof(u.turma), stdin); u.turma[strcspn(u.turma, "\n")] = 0; trim(u.turma);
            printf("Idade: "); char tmp[64]; fgets(tmp, sizeof(tmp), stdin); u.idade = atoi(tmp);
            printf("NP1: "); fgets(tmp, sizeof(tmp), stdin); u.np1 = (float)atof(tmp);
            printf("NP2: "); fgets(tmp, sizeof(tmp), stdin); u.np2 = (float)atof(tmp);
            printf("PIM: "); fgets(tmp, sizeof(tmp), stdin); u.pim = (float)atof(tmp);
            printf("Media: "); fgets(tmp, sizeof(tmp), stdin); u.media = (float)atof(tmp);
            printf("Atividade (Ativo/Inativo): "); fgets(u.atividade, sizeof(u.atividade), stdin); u.atividade[strcspn(u.atividade, "\n")] = 0; trim(u.atividade);
            if (!adicionarUsuario(&u)) printf("Falha ao adicionar usuario.\n");
        } else if (opc == 3) {
            int id; printf("ID a alterar: "); if (scanf("%d", &id)!=1) { while(getchar()!='\n'); printf("ID invalido.\n"); continue; }
            while(getchar()!='\n');
            UsuarioCSV u; memset(&u,0,sizeof(u));
            printf("AVISO: Preencha todos os campos, valores vazios serao tratados como 0/string vazia.\n");
            printf("Nome: "); fgets(u.nome, sizeof(u.nome), stdin); u.nome[strcspn(u.nome, "\n")] = 0; trim(u.nome);
            printf("Email: "); fgets(u.email, sizeof(u.email), stdin); u.email[strcspn(u.email, "\n")] = 0; trim(u.email);
            printf("Senha: "); lerSenhaOculta(u.senha, sizeof(u.senha)); trim(u.senha);
            printf("Nivel (Administrador/Coordenador/Professor/Aluno): "); fgets(u.nivel, sizeof(u.nivel), stdin); u.nivel[strcspn(u.nivel, "\n")] = 0; trim(u.nivel);
            printf("Curso: "); fgets(u.curso, sizeof(u.curso), stdin); u.curso[strcspn(u.curso, "\n")] = 0; trim(u.curso);
            printf("Turma: "); fgets(u.turma, sizeof(u.turma), stdin); u.turma[strcspn(u.turma, "\n")] = 0; trim(u.turma);
            printf("Idade: "); char tmp[64]; fgets(tmp, sizeof(tmp), stdin); u.idade = atoi(tmp);
            printf("NP1: "); fgets(tmp, sizeof(tmp), stdin); u.np1 = (float)atof(tmp);
            printf("NP2: "); fgets(tmp, sizeof(tmp), stdin); u.np2 = (float)atof(tmp);
            printf("PIM: "); fgets(tmp, sizeof(tmp), stdin); u.pim = (float)atof(tmp);
            printf("Media: "); fgets(tmp, sizeof(tmp), stdin); u.media = (float)atof(tmp);
            printf("Atividade (Ativo/Inativo): "); fgets(u.atividade, sizeof(u.atividade), stdin); u.atividade[strcspn(u.atividade, "\n")] = 0; trim(u.atividade);
            if (!alterarUsuarioPorID(id, &u)) printf("Falha ao alterar usuario.\n");
        } else if (opc == 4) {
            int id; printf("ID a excluir: "); if (scanf("%d", &id)!=1) { while(getchar()!='\n'); printf("ID invalido.\n"); continue; }
            while(getchar()!='\n');
            if (!excluirUsuarioPorID(id)) printf("Falha ao excluir usuario.\n");
        } else if (opc == 0) break;
        else printf("Opcao invalida.\n");
    }
}

void menuAdministradorUnificado(const UsuarioCSV *u) {
    int opc;
    do {
        printf("\n=== MENU ADMINISTRADOR: %s ===\n", u->nome);
        printf("1 - Meus dados\n2 - Gerenciar usuarios\n3 - Criar backup/manual\n0 - Sair\n> ");
        if (scanf("%d",&opc)!=1) { while(getchar()!='\n'); opc=-1; }
        while(getchar()!='\n');
        if (opc==1) mostrarUsuario(u);
        else if (opc==2) gerenciarUsuariosUI();
        else if (opc==3) { backupSistema(); }
        else if (opc==0) break;
        else printf("Opcao invalida.\n");
    } while (1);
}

/* ----------------- EXECUTAR SISTEMA (menu principal) ----------------- */

void executarSistema(void) {
    criarArquivoSistemaSeNaoExiste();
    initSistema();

    UsuarioCSV logado;
    char email[256], senha[128];
    int tentativas = 0;

    printf("\n==== SISTEMA ACADEMICO UNIFICADO ====\n");

    while (tentativas < 3) {
        printf("Email: ");
        if (!fgets(email, sizeof(email), stdin)) return;
        email[strcspn(email, "\n")] = 0;
        printf("Senha: ");
        lerSenhaOculta(senha, sizeof(senha));
        if (verificarLoginUnico(email, senha, &logado)) break;
        printf("Email ou senha incorretos (%d/3)\n", ++tentativas);
    }
    if (tentativas >= 3) {
        printf("Numero maximo de tentativas atingido.\n");
        return;
    }

    if (STRCASECMP(logado.nivel, "Administrador") == 0)
        menuAdministradorUnificado(&logado);
    else if (STRCASECMP(logado.nivel, "Coordenador") == 0)
        menuCoordenadorUnificado(&logado);
    else if (STRCASECMP(logado.nivel, "Professor") == 0)
        menuProfessorUnificado(&logado);
    else
        menuAlunoUnificado(&logado);
}

#endif // SISTEMAACADEMICO_H_INCLUDED

