#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include "lexer.h"

int isKeyword(char token[])
{
    if(strcmp(token, "DECLARE") == 0) return 1;
    if(strcmp(token, "INT") == 0) return 2;
    if(strcmp(token, "FLOAT") == 0) return 3;
    if(strcmp(token, "CHAR") == 0) return 4;
    if(strcmp(token, "ASSIGN") == 0) return 5;
    if(strcmp(token, "READ") == 0) return 6;
    if(strcmp(token, "PRINT") == 0) return 7;
    if(strcmp(token, "IF") == 0) return 8;
    if(strcmp(token, "ELSE") == 0) return 9;
    if(strcmp(token, "END_IF") == 0) return 10;
    if(strcmp(token, "WHILE") == 0) return 11;
    if(strcmp(token, "END_WHILE") == 0) return 12;
    if(strcmp(token, "FOR") == 0) return 13;
    if(strcmp(token, "END_FOR") == 0) return 14;

    return 0;
}

void tokenize(char input[])
{
    char temp[256];
    strncpy(temp, input, sizeof(temp) - 1);
    temp[sizeof(temp) - 1] = '\0';

    char *token = strtok(temp, " \t\r\n");

    while(token != NULL)
    {
        int type = isKeyword(token);

        switch(type)
        {
        case 1:  printf("TOKEN_DECLARE "); break;
        case 2:  printf("TOKEN_INT "); break;
        case 3:  printf("TOKEN_FLOAT "); break;
        case 4:  printf("TOKEN_CHAR "); break;
        case 5:  printf("TOKEN_ASSIGN "); break;
        case 6:  printf("TOKEN_READ "); break;
        case 7:  printf("TOKEN_PRINT "); break;
        case 8:  printf("TOKEN_IF "); break;
        case 9:  printf("TOKEN_ELSE "); break;
        case 10: printf("TOKEN_END_IF "); break;
        case 11: printf("TOKEN_WHILE "); break;
        case 12: printf("TOKEN_END_WHILE "); break;
        case 13: printf("TOKEN_FOR "); break;
        case 14: printf("TOKEN_END_FOR "); break;
        default:
            if(isdigit((unsigned char)token[0]) || (token[0] == '-' && isdigit((unsigned char)token[1])))
                printf("TOKEN_NUMBER(%s) ", token);
            else if(strcmp(token, "==") == 0 || strcmp(token, "!=") == 0 ||
                    strcmp(token, "<=") == 0 || strcmp(token, ">=") == 0 ||
                    strcmp(token, "<") == 0 || strcmp(token, ">") == 0)
                printf("TOKEN_OP(%s) ", token);
            else if(strcmp(token, "+") == 0 || strcmp(token, "-") == 0 ||
                    strcmp(token, "*") == 0 || strcmp(token, "/") == 0 || strcmp(token, "%") == 0)
                printf("TOKEN_ARITH(%s) ", token);
            else
                printf("TOKEN_IDENTIFIER(%s) ", token);
            break;
        }

        token = strtok(NULL, " \t\r\n");
    }
    printf("\n");
}