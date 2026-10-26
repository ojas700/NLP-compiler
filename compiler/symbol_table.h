#ifndef SYMBOL_TABLE_H
#define SYMBOL_TABLE_H

#define MAX_SYMBOLS 100

typedef struct
{
    char name[50];
    char type[20];
    char value[100];
    int address;
    char scope[50];
    int lod;
    int lou;
    char status[20];
} Symbol;

extern Symbol symbolTable[MAX_SYMBOLS];
extern int symbolCount;

void initSymbolTable();
int insertSymbol(char name[], char type[], char value[], char scope[], int line);
int findSymbol(char name[]);
void updateUsage(char name[], int line);
void displaySymbolTable();

#endif