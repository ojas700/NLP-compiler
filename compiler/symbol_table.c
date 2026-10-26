#include <stdio.h>
#include <string.h>
#include "symbol_table.h"

Symbol symbolTable[MAX_SYMBOLS];
int symbolCount = 0;
int nextAddress = 1000;

void initSymbolTable()
{
    symbolCount = 0;
    nextAddress = 1000;
}

int findSymbol(char name[])
{
    for(int i = 0; i < symbolCount; i++)
    {
        if(strcmp(symbolTable[i].name, name) == 0)
            return i;
    }

    return -1;
}

int insertSymbol(char name[], char type[], char value[], char scope[], int line)
{
    if(symbolCount >= MAX_SYMBOLS)
        return 0;

    if(findSymbol(name) != -1)
        return 0;

    strcpy(symbolTable[symbolCount].name, name);
    strcpy(symbolTable[symbolCount].type, type);
    strcpy(symbolTable[symbolCount].value, value);
    strcpy(symbolTable[symbolCount].scope, scope);

    symbolTable[symbolCount].address = nextAddress;
    symbolTable[symbolCount].lod = line;
    symbolTable[symbolCount].lou = line;
    strcpy(symbolTable[symbolCount].status, "Active");

    nextAddress += 4;
    symbolCount++;

    return 1;
}

void updateUsage(char name[], int line)
{
    int index = findSymbol(name);

    if(index != -1)
        symbolTable[index].lou = line;
}

void displaySymbolTable()
{
    printf("\n========== SYMBOL TABLE ==========\n");

    printf("%-12s %-10s %-12s %-10s %-12s %-6s %-6s %-10s\n",
           "Name", "Type", "Value", "Address",
           "Scope", "LOD", "LOU", "Status");

    printf("--------------------------------------------------------------------------\n");

    for(int i = 0; i < symbolCount; i++)
    {
        printf("%-12s %-10s %-12s %-10d %-12s %-6d %-6d %-10s\n",
               symbolTable[i].name,
               symbolTable[i].type,
               symbolTable[i].value,
               symbolTable[i].address,
               symbolTable[i].scope,
               symbolTable[i].lod,
               symbolTable[i].lou,
               symbolTable[i].status);
    }

    printf("==================================\n");
}