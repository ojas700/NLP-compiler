#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include "parser.h"

static void trim(char *s) {
    char *p = s;
    while(isspace((unsigned char)*p)) p++;
    if(p != s) memmove(s, p, strlen(p) + 1);
    size_t len = strlen(s);
    while(len > 0 && isspace((unsigned char)s[len - 1])) {
        s[len - 1] = '\0';
        len--;
    }
}

int parseLine(const char *input_line, int line_no, ILInstruction *inst)
{
    memset(inst, 0, sizeof(ILInstruction));
    inst->line_number = line_no;
    strncpy(inst->raw, input_line, sizeof(inst->raw) - 1);
    trim(inst->raw);

    if (strlen(inst->raw) == 0) {
        return 0; // empty line
    }

    char first[64] = {0};
    if (sscanf(inst->raw, "%63s", first) != 1) {
        return 0;
    }

    if (strcmp(first, "DECLARE") == 0) {
        inst->type = CMD_DECLARE;
        // Format: DECLARE <INT|FLOAT|CHAR> <name>
        if (sscanf(inst->raw, "DECLARE %63s %63s", inst->arg1, inst->arg2) != 2) {
            fprintf(stderr, "[PARSER ERROR Line %d] Syntax error in DECLARE: %s\n", line_no, inst->raw);
            return -1;
        }
        if (strcmp(inst->arg1, "INT") != 0 && strcmp(inst->arg1, "FLOAT") != 0 && strcmp(inst->arg1, "CHAR") != 0) {
            fprintf(stderr, "[PARSER ERROR Line %d] Unknown datatype '%s'\n", line_no, inst->arg1);
            return -1;
        }
        return 1;
    }
    else if (strcmp(first, "ASSIGN") == 0) {
        inst->type = CMD_ASSIGN;
        // Format: ASSIGN <var> <expression...>
        // Find space after var
        int offset = 0;
        if (sscanf(inst->raw, "ASSIGN %63s%n", inst->arg1, &offset) < 1) {
            fprintf(stderr, "[PARSER ERROR Line %d] Syntax error in ASSIGN: %s\n", line_no, inst->raw);
            return -1;
        }
        const char *expr_part = inst->raw + offset;
        while(isspace((unsigned char)*expr_part)) expr_part++;
        if (strlen(expr_part) == 0) {
            fprintf(stderr, "[PARSER ERROR Line %d] Missing expression in ASSIGN: %s\n", line_no, inst->raw);
            return -1;
        }
        strncpy(inst->arg2, expr_part, sizeof(inst->arg2) - 1);
        trim(inst->arg2);
        return 1;
    }
    else if (strcmp(first, "READ") == 0) {
        inst->type = CMD_READ;
        // Format: READ <var>
        if (sscanf(inst->raw, "READ %63s", inst->arg1) != 1) {
            fprintf(stderr, "[PARSER ERROR Line %d] Syntax error in READ: %s\n", line_no, inst->raw);
            return -1;
        }
        return 1;
    }
    else if (strcmp(first, "PRINT") == 0) {
        inst->type = CMD_PRINT;
        // Format: PRINT <expression or var or literal>
        const char *print_part = inst->raw + 5;
        while(isspace((unsigned char)*print_part)) print_part++;
        if (strlen(print_part) == 0) {
            fprintf(stderr, "[PARSER ERROR Line %d] Syntax error in PRINT: %s\n", line_no, inst->raw);
            return -1;
        }
        strncpy(inst->arg1, print_part, sizeof(inst->arg1) - 1);
        trim(inst->arg1);
        return 1;
    }
    else if (strcmp(first, "IF") == 0) {
        inst->type = CMD_IF;
        // Format: IF <condition>
        const char *cond_part = inst->raw + 2;
        while(isspace((unsigned char)*cond_part)) cond_part++;
        if (strlen(cond_part) == 0) {
            fprintf(stderr, "[PARSER ERROR Line %d] Missing condition in IF: %s\n", line_no, inst->raw);
            return -1;
        }
        strncpy(inst->arg1, cond_part, sizeof(inst->arg1) - 1);
        trim(inst->arg1);
        return 1;
    }
    else if (strcmp(first, "ELSE") == 0) {
        inst->type = CMD_ELSE;
        return 1;
    }
    else if (strcmp(first, "END_IF") == 0) {
        inst->type = CMD_END_IF;
        return 1;
    }
    else if (strcmp(first, "WHILE") == 0) {
        inst->type = CMD_WHILE;
        const char *cond_part = inst->raw + 5;
        while(isspace((unsigned char)*cond_part)) cond_part++;
        if (strlen(cond_part) == 0) {
            fprintf(stderr, "[PARSER ERROR Line %d] Missing condition in WHILE: %s\n", line_no, inst->raw);
            return -1;
        }
        strncpy(inst->arg1, cond_part, sizeof(inst->arg1) - 1);
        trim(inst->arg1);
        return 1;
    }
    else if (strcmp(first, "END_WHILE") == 0) {
        inst->type = CMD_END_WHILE;
        return 1;
    }
    else if (strcmp(first, "FOR") == 0) {
        inst->type = CMD_FOR;
        // Format: FOR <var> <start> <end>
        if (sscanf(inst->raw, "FOR %63s %63s %127s", inst->arg1, inst->arg2, inst->arg3) != 3) {
            fprintf(stderr, "[PARSER ERROR Line %d] Syntax error in FOR: %s\n", line_no, inst->raw);
            return -1;
        }
        return 1;
    }
    else if (strcmp(first, "END_FOR") == 0) {
        inst->type = CMD_END_FOR;
        return 1;
    }
    else {
        fprintf(stderr, "[PARSER ERROR Line %d] Unrecognized intermediate command '%s'\n", line_no, first);
        return -1;
    }
}