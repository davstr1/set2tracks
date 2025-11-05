import { PrismaClient } from '@prisma/client';
import prisma from '../utils/database';

/**
 * Base Repository
 * Provides common CRUD operations for all repositories
 */
export abstract class BaseRepository<T> {
  protected prisma: PrismaClient;
  protected modelName: string;

  constructor(modelName: string) {
    this.prisma = prisma;
    this.modelName = modelName;
  }

  /**
   * Find a single record by ID
   */
  async findById(id: number, include?: Record<string, unknown>): Promise<T | null> {
    const model = (this.prisma as any)[this.modelName];
    return model.findUnique({
      where: { id },
      ...(include && { include }),
    });
  }

  /**
   * Find all records with optional filters
   */
  async findAll(options?: {
    where?: Record<string, unknown>;
    include?: Record<string, unknown>;
    orderBy?: Record<string, unknown>;
    skip?: number;
    take?: number;
  }): Promise<T[]> {
    const model = (this.prisma as any)[this.modelName];
    return model.findMany(options || {});
  }

  /**
   * Count records with optional filters
   */
  async count(where?: Record<string, unknown>): Promise<number> {
    const model = (this.prisma as any)[this.modelName];
    return model.count({ where });
  }

  /**
   * Create a new record
   */
  async create(data: Record<string, unknown>): Promise<T> {
    const model = (this.prisma as any)[this.modelName];
    return model.create({ data });
  }

  /**
   * Update a record by ID
   */
  async update(id: number, data: Record<string, unknown>): Promise<T> {
    const model = (this.prisma as any)[this.modelName];
    return model.update({
      where: { id },
      data,
    });
  }

  /**
   * Delete a record by ID
   */
  async delete(id: number): Promise<T> {
    const model = (this.prisma as any)[this.modelName];
    return model.delete({
      where: { id },
    });
  }

  /**
   * Find a single record by unique field
   */
  async findUnique(where: Record<string, unknown>, include?: Record<string, unknown>): Promise<T | null> {
    const model = (this.prisma as any)[this.modelName];
    return model.findUnique({
      where,
      ...(include && { include }),
    });
  }

  /**
   * Upsert a record
   */
  async upsert(
    where: Record<string, unknown>,
    create: Record<string, unknown>,
    update: Record<string, unknown>
  ): Promise<T> {
    const model = (this.prisma as any)[this.modelName];
    return model.upsert({
      where,
      create,
      update,
    });
  }

  /**
   * Find first record matching criteria
   */
  async findFirst(options?: {
    where?: Record<string, unknown>;
    include?: Record<string, unknown>;
    orderBy?: Record<string, unknown>;
  }): Promise<T | null> {
    const model = (this.prisma as any)[this.modelName];
    return model.findFirst(options || {});
  }
}
