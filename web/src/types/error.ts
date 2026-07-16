export class AppError extends Error {
  constructor(
    public detail: string,
    public code: number,
    public statusCode: number,
  ) {
    super(detail)
    this.name = 'AppError'
  }
}
